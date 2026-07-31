from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Mapping, TextIO
from uuid import uuid4

from autonomy.configuration.loader import RecordingConfiguration
from autonomy.sensing.synchronization import SynchronizedMeasurements
from autonomy.simulation.carla.geometry import VehicleGeometry


class RecorderError(RuntimeError):
    """Çalışma kaydı başlatılamadığında veya yazılamadığında üretilir."""


class RunRecorder:
    """Manifest ve frame indeksini düşük maliyetli, satır bazlı biçimde kaydeder."""

    def __init__(self, configuration: RecordingConfiguration) -> None:
        self._configuration = configuration
        self._run_directory: Path | None = None
        self._manifest_path: Path | None = None
        self._frames_file: TextIO | None = None
        self._manifest: dict[str, Any] = {}
        self._frame_count = 0

    @property
    def run_directory(self) -> Path | None:
        return self._run_directory

    def start(
        self,
        *,
        configuration_hash: str,
        configuration_sources: Mapping[str, str],
        map_name: str,
        client_version: str,
        server_version: str,
        compatibility_version: str,
        vehicle_id: str,
        vehicle_blueprint: str,
        vehicle_role_name: str,
        vehicle_actor_id: int,
        sensor_layout_id: str,
        reference_frame: str,
        geometry: VehicleGeometry,
        sensor_descriptions: tuple[Mapping[str, Any], ...],
        fixed_delta_seconds: float,
    ) -> None:
        if not self._configuration.enabled:
            return
        if self._frames_file is not None:
            raise RecorderError("Recorder zaten başlatıldı.")

        started_at = datetime.now(UTC)
        run_id = f"{started_at:%Y%m%dT%H%M%S.%fZ}-{uuid4().hex[:8]}"
        run_directory = self._configuration.output_directory / run_id
        try:
            run_directory.mkdir(parents=True, exist_ok=False)
            frames_path = run_directory / "frames.jsonl"
            self._frames_file = frames_path.open("x", encoding="utf-8", buffering=1)
        except OSError as exc:
            raise RecorderError(f"Recorder dizini oluşturulamadı: {run_directory}") from exc

        self._run_directory = run_directory
        self._manifest_path = run_directory / "manifest.json"
        self._frame_count = 0
        self._manifest = {
            "schema_version": "1.0",
            "run_id": run_id,
            "status": "RUNNING",
            "started_at_utc": started_at.isoformat(),
            "completed_at_utc": None,
            "configuration_hash": configuration_hash,
            "configuration_sources": dict(configuration_sources),
            "carla": {
                "client_version": client_version,
                "server_version": server_version,
                "compatibility_version": compatibility_version,
                "map_name": map_name,
                "fixed_delta_seconds": fixed_delta_seconds,
                "synchronous_mode": True,
            },
            "vehicle": {
                "vehicle_id": vehicle_id,
                "blueprint": vehicle_blueprint,
                "role_name": vehicle_role_name,
                "actor_id": vehicle_actor_id,
                "geometry": geometry.as_dict(),
            },
            "sensor_layout": {
                "layout_id": sensor_layout_id,
                "reference_frame": reference_frame,
            },
            "sensors": list(sensor_descriptions),
            "record_raw_data": self._configuration.record_raw_data,
            "frame_count": 0,
        }
        try:
            self._write_manifest()
        except Exception:
            if self._frames_file is not None:
                self._frames_file.close()
                self._frames_file = None
            raise

    def record(
        self,
        synchronized: SynchronizedMeasurements,
        vehicle_feedback: Mapping[str, Any],
    ) -> None:
        if not self._configuration.enabled:
            return
        if self._frames_file is None or self._run_directory is None:
            raise RecorderError("Recorder başlatılmadan frame yazılamaz.")

        contract = synchronized.contract
        sensor_entries: dict[str, dict[str, Any]] = {}
        for sensor_id, measurement in synchronized.measurements_by_sensor_id.items():
            raw_path = None
            if self._configuration.record_raw_data:
                raw_path = self._write_raw(sensor_id, measurement.frame, measurement.payload)
            sensor_entries[sensor_id] = {
                "sensor_type": measurement.sensor_type,
                "timestamp_seconds": measurement.timestamp_seconds,
                "payload_size_bytes": measurement.payload_size_bytes,
                "encoding": measurement.encoding,
                "raw_path": raw_path,
            }

        record = {
            "schema_version": contract.metadata.schema_version,
            "sequence_number": contract.metadata.sequence_number,
            "simulation_frame": contract.metadata.simulation_frame,
            "timestamp_seconds": contract.metadata.timestamp_seconds,
            "configuration_hash": contract.metadata.configuration_hash,
            "sensors": sensor_entries,
            "vehicle_feedback": dict(vehicle_feedback),
        }
        try:
            self._frames_file.write(json.dumps(record, sort_keys=True) + "\n")
        except OSError as exc:
            raise RecorderError("frames.jsonl yazılamadı.") from exc
        self._frame_count += 1
        if self._frame_count % self._configuration.flush_every_frames == 0:
            self._frames_file.flush()
            self._manifest["frame_count"] = self._frame_count
            self._write_manifest()

    def stop(self, status: str = "COMPLETED") -> None:
        if not self._configuration.enabled:
            return
        if self._frames_file is None:
            return
        try:
            self._frames_file.flush()
            self._frames_file.close()
        finally:
            self._frames_file = None
        self._manifest["status"] = status
        self._manifest["completed_at_utc"] = datetime.now(UTC).isoformat()
        self._manifest["frame_count"] = self._frame_count
        self._write_manifest()

    def _write_raw(self, sensor_id: str, frame: int, payload: Any) -> str | None:
        raw_data = getattr(payload, "raw_data", None)
        if raw_data is None or self._run_directory is None:
            return None
        relative_path = Path("raw") / sensor_id / f"{frame:010d}.bin"
        target = self._run_directory / relative_path
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(bytes(raw_data))
        except (OSError, TypeError) as exc:
            raise RecorderError(f"Ham sensör verisi yazılamadı: {relative_path}") from exc
        return relative_path.as_posix()

    def _write_manifest(self) -> None:
        if self._manifest_path is None:
            return
        temporary = self._manifest_path.with_suffix(".json.tmp")
        try:
            temporary.write_text(
                json.dumps(self._manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            temporary.replace(self._manifest_path)
        except OSError as exc:
            raise RecorderError(f"Manifest yazılamadı: {self._manifest_path}") from exc
