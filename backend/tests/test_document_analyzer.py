import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.document_analyzer import analyze_document_background_task
from app.models.generation import (
    TaskGenerationSchema, GeneratedTask,
    QuizGenerationSchema, QuizQuestionSchema,
    CheatsheetGenerationSchema, TagGenerationSchema
)

@pytest.mark.asyncio
async def test_empty_pdf_aborts_early():
    """Test that if PyMuPDF returns no text, the analysis aborts early."""
    # Mock PyMuPDF to return a document with one empty page
    mock_doc = MagicMock()
    mock_doc.__len__.return_value = 1
    mock_page = MagicMock()
    mock_page.get_text.return_value = "   \n  "  # Only whitespace
    mock_doc.__getitem__.return_value = mock_page

    with patch("app.services.document_analyzer.pymupdf.open", return_value=mock_doc), \
         patch("app.services.document_analyzer.AsyncSessionLocal") as mock_db_cls:
        
        await analyze_document_background_task("doc_123", "dummy.pdf", "user_1")
        
        # Verify db was created but no commits were made because it returned early
        mock_db = mock_db_cls.return_value.__aenter__.return_value
        mock_db.commit.assert_not_called()

@pytest.mark.asyncio
async def test_successful_analysis_pipeline():
    """Test that a document with text goes through the entire AI pipeline and saves to DB."""
    # 1. Mock PyMuPDF
    mock_doc = MagicMock()
    mock_doc.__len__.return_value = 1
    mock_page = MagicMock()
    mock_page.get_text.return_value = "This is a dummy study document about biology."
    mock_doc.__getitem__.return_value = mock_page

    # 2. Mock Database Session
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    # Mock db.execute().scalars().first() to simulate existing Subject/Topic
    mock_result = MagicMock()
    mock_subject = MagicMock(subject_id="sub_1")
    mock_result.scalars().first.return_value = mock_subject
    mock_db.execute.return_value = mock_result
    
    mock_db_cls = MagicMock()
    mock_db_cls.return_value.__aenter__.return_value = mock_db

    # 3. Mock OpenAI Client
    mock_parsed_tasks = TaskGenerationSchema(
        tasks=[GeneratedTask(difficulty=1, task_text="Task 1", key_concepts=["Bio"])]
    )
    mock_parsed_quiz = QuizGenerationSchema(
        title="Bio Quiz",
        questions=[QuizQuestionSchema(question_text="Q1", options=["A", "B", "C", "D"], correct_answer="A", explanation="Expl", key_concepts=["Bio"])]
    )
    mock_parsed_cheatsheet = CheatsheetGenerationSchema(
        title="Bio Cheat",
        content="# Cheatsheet\nBio is cool",
        key_concepts=["Biology"]
    )
    mock_parsed_tags = TagGenerationSchema(
        tags=["Biology", "Science"]
    )

    mock_client = AsyncMock()
    # Mock the parse method to return different parsed schemas in sequence
    mock_completion_tags = MagicMock()
    mock_completion_tags.choices[0].message.parsed = mock_parsed_tags
    mock_completion_tasks = MagicMock()
    mock_completion_tasks.choices[0].message.parsed = mock_parsed_tasks
    
    mock_completion_quiz = MagicMock()
    mock_completion_quiz.choices[0].message.parsed = mock_parsed_quiz
    
    mock_completion_cheatsheet = MagicMock()
    mock_completion_cheatsheet.choices[0].message.parsed = mock_parsed_cheatsheet

    mock_client.beta.chat.completions.parse = AsyncMock(side_effect=[
        mock_completion_tags,
        mock_completion_tasks,
        mock_completion_quiz,
        mock_completion_cheatsheet
    ])

    with patch("app.services.document_analyzer.pymupdf.open", return_value=mock_doc), \
         patch("app.services.document_analyzer.AsyncSessionLocal", mock_db_cls), \
         patch("app.services.document_analyzer.client", mock_client), \
         patch("app.services.document_analyzer.manager.send_personal_message", new_callable=AsyncMock) as mock_send:
        
        await analyze_document_background_task("doc_123", "dummy.pdf", "user_1")

        # Verify Database interactions
        # 1 Task + 1 Quiz + 1 QuizQuestion + 1 Cheatsheet = 4 calls to db.add
        assert mock_db.add.call_count == 4
        mock_db.commit.assert_awaited()

        # Verify WebSocket notification
        mock_send.assert_awaited_once_with("user_1", {
            "type": "DOCUMENT_ANALYZED",
            "message": "doc_123",
            "document_id": "doc_123",
        })

@pytest.mark.asyncio
async def test_openai_failure_rollback():
    """Test that if the database commit fails, the transaction is rolled back."""
    mock_doc = MagicMock()
    mock_doc.__len__.return_value = 1
    mock_page = MagicMock()
    mock_page.get_text.return_value = "Valid text"
    mock_doc.__getitem__.return_value = mock_page

    mock_db = AsyncMock()
    
    # Mock db.execute().scalars().first() to simulate existing Subject/Topic
    mock_result = MagicMock()
    mock_subject = MagicMock(subject_id="sub_bad")
    mock_result.scalars().first.return_value = mock_subject
    mock_db.execute.return_value = mock_result
    
    # Force db.commit to raise an exception
    mock_db.commit.side_effect = Exception("Database is down!")
    
    mock_db_cls = MagicMock()
    mock_db_cls.return_value.__aenter__.return_value = mock_db

    mock_client = AsyncMock()
    mock_completion = MagicMock()
    mock_completion.choices[0].message.parsed = None
    mock_client.beta.chat.completions.parse = AsyncMock(return_value=mock_completion)

    with patch("app.services.document_analyzer.pymupdf.open", return_value=mock_doc), \
         patch("app.services.document_analyzer.AsyncSessionLocal", mock_db_cls), \
         patch("app.services.document_analyzer.client", mock_client), \
         patch("app.services.document_analyzer.manager.send_personal_message", new_callable=AsyncMock) as mock_send:
        
        await analyze_document_background_task("doc_bad", "bad.pdf", "user_2")
        
        mock_db.commit.assert_awaited()
        mock_db.rollback.assert_awaited_once()
        # A failed commit must still produce one explicit failure notification.
        mock_send.assert_awaited_once()


@pytest.mark.asyncio
async def test_generation_failure_is_not_reported_as_success():
    mock_doc = MagicMock()
    mock_doc.__len__.return_value = 1
    mock_page = MagicMock()
    mock_page.get_text.return_value = "Readable exercise text"
    mock_doc.__getitem__.return_value = mock_page

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db_cls = MagicMock()
    mock_db_cls.return_value.__aenter__.return_value = mock_db

    mock_client = AsyncMock()
    mock_client.beta.chat.completions.parse = AsyncMock(side_effect=RuntimeError("provider unavailable"))
    mock_client.embeddings.create = AsyncMock(side_effect=RuntimeError("embeddings unavailable"))

    with patch("app.services.document_analyzer.pymupdf.open", return_value=mock_doc), \
         patch("app.services.document_analyzer.AsyncSessionLocal", mock_db_cls), \
         patch("app.services.document_analyzer.client", mock_client), \
         patch("app.services.document_analyzer.manager.send_personal_message", new_callable=AsyncMock) as mock_send:
        await analyze_document_background_task("doc_failed", "failed.pdf", "user_3")

    mock_send.assert_awaited_once()
    notification = mock_send.await_args.args[1]
    assert notification["type"] == "DOCUMENT_ANALYSIS_FAILED"
    assert notification["document_id"] == "doc_failed"
