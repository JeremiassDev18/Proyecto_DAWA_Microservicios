from unittest.mock import MagicMock, patch

import pytest

from app.db import queries
from app.services.search_service import hybrid_search


class TestHybridSearch:
    def test_returns_response_on_match(self):
        with patch.object(queries, 'search_hybrid',
                          return_value=[(1, "texto", 2, "INTENT", 0.85)]):
            with patch.object(queries, 'get_respuesta_by_intencion',
                              return_value=(42, "Respuesta encontrada",
                                            "texto", 1, 0)):
                with patch.object(queries, 'increment_veces_usada'):
                    with patch("app.services.search_service.generate_embedding",
                               return_value=[0.1] * 384):
                        result = hybrid_search(MagicMock(), "test query")

        assert result == "Respuesta encontrada"

    def test_returns_none_on_no_results(self):
        with patch.object(queries, 'search_hybrid', return_value=[]):
            with patch("app.services.search_service.generate_embedding",
                       return_value=[0.1] * 384):
                result = hybrid_search(MagicMock(), "test query")

        assert result is None

    def test_returns_none_on_low_score(self):
        with patch.object(queries, 'search_hybrid',
                          return_value=[(1, "texto", 2, "INTENT", 0.3)]):
            with patch("app.services.search_service.generate_embedding",
                       return_value=[0.1] * 384):
                result = hybrid_search(MagicMock(), "test query")

        assert result is None

    def test_returns_none_on_no_respuesta(self):
        with patch.object(queries, 'search_hybrid',
                          return_value=[(1, "texto", 2, "INTENT", 0.85)]):
            with patch.object(queries, 'get_respuesta_by_intencion',
                              return_value=None):
                with patch("app.services.search_service.generate_embedding",
                           return_value=[0.1] * 384):
                    result = hybrid_search(MagicMock(), "test query")

        assert result is None

    def test_increments_usage_count(self):
        with patch.object(queries, 'search_hybrid',
                          return_value=[(1, "texto", 2, "INTENT", 0.85)]):
            with patch.object(queries, 'get_respuesta_by_intencion',
                              return_value=(42, "Respuesta", "texto", 1, 3)):
                with patch.object(queries, 'increment_veces_usada') as mock_inc:
                    with patch("app.services.search_service.generate_embedding",
                               return_value=[0.1] * 384):
                        hybrid_search(MagicMock(), "test query")

        mock_inc.assert_called_once()
        args = mock_inc.call_args[0]
        assert args[1] == 42
