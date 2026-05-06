from app.domain.semantic import TokenSimilarity


def test_token_similarity_scores_related_text_higher_than_unrelated_text():
    similarity = TokenSimilarity()

    related = similarity.score("create-order failed contract_validation 400", "create-order 400 contract_validation")
    unrelated = similarity.score("create-order failed contract_validation 400", "login passed 200")

    assert related > unrelated
    assert related > 0

