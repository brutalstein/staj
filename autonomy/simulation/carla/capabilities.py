from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CarlaCapabilities:
    version: str
    supports_server_version_query: bool
    supports_semantic_lidar: bool
    supports_optical_flow_camera: bool


_CAPABILITIES: dict[str, CarlaCapabilities] = {
    "0.9.15": CarlaCapabilities("0.9.15", True, True, True),
    "0.9.16": CarlaCapabilities("0.9.16", True, True, True),
}


def capabilities_for(version: str) -> CarlaCapabilities:
    try:
        return _CAPABILITIES[{"e78db150c": "0.9.16"}.get(version, version)]
    except KeyError as exc:
        raise ValueError(f"Desteklenmeyen CARLA sürümü: {version}") from exc
