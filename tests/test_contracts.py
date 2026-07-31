from autonomy.contracts.common import MessageMetadata
from autonomy.contracts.planning import LongitudinalProfile, SpeedConstraintSet


def metadata() -> MessageMetadata:
    return MessageMetadata(
        timestamp_seconds=1.0,
        simulation_frame=50,
        sequence_number=4,
        coordinate_frame="ego_rear_axle",
        source_module="test",
    )


def test_speed_constraint_rejects_inverted_bounds() -> None:
    try:
        SpeedConstraintSet(
            metadata=metadata(),
            desired_free_flow_speed_mps=10.0,
            maximum_allowed_speed_mps=5.0,
            minimum_allowed_speed_mps=6.0,
        )
    except ValueError as exc:
        assert "Minimum hız" in str(exc)
    else:
        raise AssertionError("Geçersiz hız zarfı kabul edildi.")


def test_longitudinal_profile_requires_equal_lengths() -> None:
    try:
        LongitudinalProfile(
            metadata=metadata(),
            time_seconds=(0.0, 0.1),
            speed_mps=(1.0,),
            acceleration_mps2=(0.0, 0.0),
            jerk_mps3=(0.0, 0.0),
            active_constraints=(),
        )
    except ValueError as exc:
        assert "aynı uzunlukta" in str(exc)
    else:
        raise AssertionError("Uyumsuz profil dizileri kabul edildi.")
