from __future__ import annotations

import logging
import re
import time
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

from rag.config import RagConfig
from rag.generation.prompts import SYSTEM_PROMPT, build_context

LOG = logging.getLogger("rag.generation")


def answer_question(config: RagConfig, question: str, docs: list, retrieval_debug: dict | None = None) -> dict[str, Any]:
    retrieval_debug = retrieval_debug or {}
    start = time.perf_counter()

    if not docs:
        return _unknown_response(retrieval_debug, timing_ms={"generate": 0})

    context, citations = build_context(docs, max_chars=config.context_max_chars)
    if not context or not citations:
        return _unknown_response(retrieval_debug, timing_ms={"generate": 0})

    answer_text, prompt_size = _generate_answer(question, context, config)

    if _is_unknown(answer_text):
        return _unknown_response(retrieval_debug, timing_ms={"generate": elapsed_ms(start)})

    if not _has_citation(answer_text):
        answer_text = f"{answer_text.rstrip()} [{citations[0]['source']}]"

    response = {
        "answer": answer_text,
        "citations": citations,
        "debug": {
            "retrieval": retrieval_debug,
            "timing_ms": {"generate": elapsed_ms(start)},
            "prompt_tokens": prompt_size,
        },
    }
    LOG.info("query.generate citations=%s chars=%s", len(citations), len(answer_text))
    return response


def _generate_answer(question: str, context: str, config: RagConfig) -> tuple[str, int]:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "Question:\n{question}\n\nContext:\n{context}\n\nAnswer:"),
        ]
    )

    llm = _build_chat_model(config)
    chain = (
        RunnablePassthrough()
        | {
            "question": RunnableLambda(lambda x: x["question"]),
            "context": RunnableLambda(lambda x: x["context"]),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    payload = {"question": question, "context": context}
    answer = chain.invoke(payload)
    prompt_size = max(1, (len(context) + len(question)) // 4)
    return str(answer).strip(), prompt_size


def _build_chat_model(config: RagConfig):
    if config.openai_api_key:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=config.chat_model, api_key=config.openai_api_key, temperature=0)

    return RunnableLambda(lambda x: _local_grounded_answer(x.to_string() if hasattr(x, "to_string") else str(x)))


def _local_grounded_answer(prompt_text: str) -> str:
    sources = re.findall(r"\[([^\]]+)\]", prompt_text)
    source = sources[0] if sources else "unknown"
    context_match = re.search(r"Context:\n(.*)\n\nAnswer:", prompt_text, flags=re.DOTALL)
    context = context_match.group(1).strip() if context_match else ""
    if not context:
        return "I don't know based on the provided documents."
    first_line = next((line for line in context.splitlines() if line.strip()), "")
    return f"{first_line[:400]} [{source}]"


def _unknown_response(retrieval_debug: dict, timing_ms: dict[str, int]) -> dict[str, Any]:
    return {
        "answer": "I don't know based on the provided documents.",
        "citations": [],
        "debug": {
            "retrieval": retrieval_debug,
            "timing_ms": timing_ms,
            "prompt_tokens": 0,
        },
    }


def _is_unknown(text: str) -> bool:
    return text.strip() == "I don't know based on the provided documents."


def _has_citation(text: str) -> bool:
    return bool(re.search(r"\[[^\]]+\]", text))


def elapsed_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)
