import pytest

from positive_emotion_engine.physionet_stress_dataset import (
    DatasetContractError,
    participant_data_policy,
    parse_event_tags,
    parse_regular_empatica_stream,
    parse_stress_level_csv,
    stream_start_offset_seconds,
)


def test_v2_label_parser_preserves_stage_semantics_and_zero_values():
    text = ",Baseline,TMCT,First Rest,Real Opinion,Opposite Opinion,Second Rest,Subtract\n" \
           "f01,0.00,5.00,2.00,3.00,4.00,2.00,3.00\n"
    labels = parse_stress_level_csv(text, "v2")
    assert [x.stage for x in labels] == [
        "Baseline", "TMCT", "First Rest", "Real Opinion",
        "Opposite Opinion", "Second Rest", "Subtract"
    ]
    assert labels[0].self_reported_stress == 0.0
    assert labels[1].self_reported_stress == 5.0


def test_v1_and_v2_headers_are_not_silently_merged():
    v1 = ",Baseline,Stroop,First Rest,TMCT,Second Rest,Real Opinion,Opposite Opinion,Subtract\n" \
         "S01,3,4.5,4,4,5.5,6,7,7\n"
    assert len(parse_stress_level_csv(v1, "v1")) == 8
    with pytest.raises(DatasetContractError):
        parse_stress_level_csv(v1, "v2")


def test_known_recording_caveats_produce_explicit_exclusion_policy():
    assert participant_data_policy("S02").use_for_model_validation is False
    assert participant_data_policy("f07").reason is not None
    assert participant_data_policy("f14").use_for_model_validation is False
    assert participant_data_policy("f10").use_for_model_validation is True


def test_tags_must_be_monotonic():
    tags = parse_event_tags("2013-06-30 10:03:33\n2013-06-30 10:05:22\n")
    assert len(tags) == 2
    with pytest.raises(DatasetContractError):
        parse_event_tags("2013-06-30 10:05:22\n2013-06-30 10:03:33\n")


def test_regular_stream_parser_honors_sample_rate_and_format():
    stream = parse_regular_empatica_stream(
        "2013-06-30 09:59:54\n1.0\n78.0\n77.0\n76.67\n",
        unit="bpm",
        expected_sample_rate_hz=1.0,
    )
    assert stream.sample_rate_hz == 1.0
    assert stream.values == (78.0, 77.0, 76.67)
    assert stream.duration_seconds == 3.0


def test_streams_keep_independent_start_times_and_report_offset():
    eda = parse_regular_empatica_stream(
        "2013-06-30 09:59:50\n4.0\n1.0\n1.1\n1.2\n",
        unit="uS",
        expected_sample_rate_hz=4.0,
    )
    hr = parse_regular_empatica_stream(
        "2013-06-30 09:59:54\n1.0\n78.0\n77.0\n",
        unit="bpm",
        expected_sample_rate_hz=1.0,
    )
    assert eda.session_start_utc != hr.session_start_utc
    assert stream_start_offset_seconds(eda, hr) == 4.0
