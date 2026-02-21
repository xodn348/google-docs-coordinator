from unittest.mock import Mock

from src.models.coordination_models import Decision, NextStep, Question
from src.services.ai_analyzer import AIAnalyzer, CoordinationAnalysis


def test_ai_analyzer_init_uses_api_key(mock_settings, mocker):
    openai_cls = mocker.patch("src.services.ai_analyzer.OpenAI")

    AIAnalyzer(mock_settings)

    openai_cls.assert_called_once_with(api_key="sk-test-key")


def test_analyze_returns_structured_output(
    mock_settings, sample_comment, sample_revision, sample_metadata, mocker
):
    parse = Mock()
    openai_client = Mock()
    openai_client.beta.chat.completions.parse = parse
    mocker.patch("src.services.ai_analyzer.OpenAI", return_value=openai_client)

    analysis = CoordinationAnalysis(
        questions=[Question(text="What next?", author="Alice", priority="high")],
        decisions=[Decision(summary="Use React", decided_by="Alice")],
        next_steps=[NextStep(description="Finalize scope", assignee="Bob")],
    )
    parse.return_value = Mock(choices=[Mock(message=Mock(parsed=analysis))])

    analyzer = AIAnalyzer(mock_settings)
    questions, decisions, next_steps, error = analyzer.analyze(
        [sample_comment], [sample_revision], sample_metadata
    )

    assert error is None
    assert len(questions) == 1
    assert len(decisions) == 1
    assert len(next_steps) == 1
    assert parse.call_args.kwargs["response_format"] is CoordinationAnalysis


def test_analyze_uses_fallback_metadata_when_none(
    mock_settings, sample_comment, sample_revision, mocker
):
    parse = Mock(
        return_value=Mock(choices=[Mock(message=Mock(parsed=CoordinationAnalysis()))])
    )
    openai_client = Mock()
    openai_client.beta.chat.completions.parse = parse
    mocker.patch("src.services.ai_analyzer.OpenAI", return_value=openai_client)
    build_user_prompt = mocker.patch(
        "src.services.ai_analyzer.build_user_prompt", return_value="prompt"
    )

    analyzer = AIAnalyzer(mock_settings)
    analyzer.analyze([sample_comment], [sample_revision], None)

    metadata_arg = build_user_prompt.call_args.args[2]
    assert metadata_arg.document_id == "unknown"
    assert metadata_arg.title == "Unknown Document"


def test_analyze_returns_error_when_parsed_payload_is_none(
    mock_settings, sample_metadata, mocker
):
    parse = Mock(return_value=Mock(choices=[Mock(message=Mock(parsed=None))]))
    openai_client = Mock()
    openai_client.beta.chat.completions.parse = parse
    mocker.patch("src.services.ai_analyzer.OpenAI", return_value=openai_client)

    analyzer = AIAnalyzer(mock_settings)
    questions, decisions, next_steps, error = analyzer.analyze([], [], sample_metadata)

    assert questions == []
    assert decisions == []
    assert next_steps == []
    assert error is not None
    assert "AI analysis failed" in error


def test_analyze_returns_error_when_openai_raises(
    mock_settings, sample_metadata, mocker
):
    parse = Mock(side_effect=RuntimeError("openai down"))
    openai_client = Mock()
    openai_client.beta.chat.completions.parse = parse
    mocker.patch("src.services.ai_analyzer.OpenAI", return_value=openai_client)

    analyzer = AIAnalyzer(mock_settings)
    questions, decisions, next_steps, error = analyzer.analyze([], [], sample_metadata)

    assert questions == []
    assert decisions == []
    assert next_steps == []
    assert error is not None
    assert "openai down" in error


def test_analyze_sends_system_and_user_messages(mock_settings, sample_metadata, mocker):
    parse = Mock(
        return_value=Mock(choices=[Mock(message=Mock(parsed=CoordinationAnalysis()))])
    )
    openai_client = Mock()
    openai_client.beta.chat.completions.parse = parse
    mocker.patch("src.services.ai_analyzer.OpenAI", return_value=openai_client)
    mocker.patch(
        "src.services.ai_analyzer.build_user_prompt", return_value="built prompt"
    )

    analyzer = AIAnalyzer(mock_settings)
    analyzer.analyze([], [], sample_metadata)

    messages = parse.call_args.kwargs["messages"]
    assert messages[0]["role"] == "system"
    assert messages[1] == {"role": "user", "content": "built prompt"}
