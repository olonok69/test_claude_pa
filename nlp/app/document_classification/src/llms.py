import transformers
from langchain_community.llms import HuggingFacePipeline


def create_langchain_llm_task(
    model,
    tokenizer,
    task: str = "summarization",
    temperature: float = 0.2,
    repetition_penalty: float = 1.1,
    max_new_tokens: int = 2000,
):
    """
    Create langchain Huggingface Pipeline
    """

    # Text Summarization Pipeline
    text_summarization_pipeline = transformers.pipeline(
        model=model,
        tokenizer=tokenizer,
        task=task,
        temperature=temperature,
        repetition_penalty=repetition_penalty,
        max_new_tokens=max_new_tokens,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.eos_token_id,
    )
    llm = HuggingFacePipeline(pipeline=text_summarization_pipeline)
    return llm
