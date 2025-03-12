def get_shortened_body(body: str, max_words: int = 10, max_chars: int = 50) -> str:
    """
    Обрезает текст до указанного количества слов или символов.
    Добавляет многоточие (...) в конце, если текст был обрезан.
    """
    words = body.split()
    shortened_body = " ".join(words[:max_words])  # Берем первые max_words слов
    if len(shortened_body) > max_chars:  # Если длина превышает max_chars,
        # обрезаем
        shortened_body = shortened_body[:max_chars]
    if shortened_body != body:  # Если текст был обрезан, добавляем многоточие
        shortened_body += "..."
    return shortened_body


def replace_placeholder(text: str, name: str) -> str:
    """
    Заменяет заглушку #name на указанное имя.
    Если #name отсутствует, возвращает исходный текст.
    """
    return text.replace("#name", name)