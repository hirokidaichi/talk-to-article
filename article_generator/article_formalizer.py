from typing import List, Optional
import streamlit as st
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from .transcript_splitter import split_transcript

def create_prompt_template(with_context: bool = False) -> str:
    """
    プロンプトテンプレートを作成します。
    
    Args:
        with_context: 前のチャンクのコンテキストを含めるかどうか
    
    Returns:
        プロンプトテンプレート
    """
    base_template = """
    <system_role>
    あなたは文字起こしテキストを整理して整文化をするプロフェッショナルです。
    以下の文字起こしテキストを、背景情報も考慮しながら整理された会話の発言録に書き直してください。
    </system_role>

    <input_transcript>
    {chunk}
    </input_transcript>
    
    <background_info>
    {background}
    </background_info>
    
    <processing_instructions>
    - 話者の発言を明確に区別し、「話者A:」「話者B:」などのラベルを付けてください
    - 話者が特定できる場合は、名前や役職を使用してください
    - 文法的に正しく、読みやすい文章に整えてください
    - 冗長な表現、言い間違い、言い直しを整理してください
    - 「えー」「あの」などの無意味な言葉を削除してください
    - 文脈から明らかな場合は、省略された主語や目的語を補ってください
    - 専門用語や略語はそのまま使用してください
    - 背景情報を参考にして、文脈を理解しやすくしてください
    - マークダウン形式で出力してください
    - 元の内容や意味を変えないでください
    </processing_instructions>
    """
    
    context_template = """
    <previous_content>
    {previous_result}
    </previous_content>
    
    <additional_instructions>
    - 前の部分との一貫性を保ってください
    - 同じ話者には同じラベルを使用してください
    - 話の流れが自然につながるようにしてください
    - 重複する内容は適切に調整してください
    </additional_instructions>
    """
    
    if with_context:
        return base_template + context_template
    else:
        return base_template

def get_anthropic_client(model_name: str = "claude-3-7-sonnet-latest") -> ChatAnthropic:
    """
    Anthropicクライアントを取得します。
    
    Args:
        model_name: 使用するAnthropicモデル名
    
    Returns:
        ChatAnthropicインスタンス
    """
    api_key = st.session_state.get("anthropic_api_key")
    return ChatAnthropic(model=model_name, anthropic_api_key=api_key)

def formalize_chunk(chunk: str, background: Optional[str] = None, model_name: str = "claude-3-7-sonnet-latest") -> str:
    """
    文字起こしチャンクを整文化します。
    
    Args:
        chunk: 整文化する文字起こしチャンク
        background: 背景情報（オプション）
        model_name: 使用するAnthropicモデル名
    
    Returns:
        整文化されたテキスト
    """
    # Anthropicモデルの初期化
    llm = get_anthropic_client(model_name)
    
    # プロンプトテンプレートの作成
    template = create_prompt_template(with_context=False)
    prompt = ChatPromptTemplate.from_template(template)
    
    # 最新のLangChain APIを使用
    chain = prompt | llm
    result = chain.invoke({"chunk": chunk, "background": background if background else ""})
    
    return result.content

def formalize_with_context(chunk: str, previous_result: str = "", background: Optional[str] = None, model_name: str = "claude-3-7-sonnet-latest") -> str:
    """
    前のチャンクの処理結果を考慮して、文字起こしチャンクを整文化します。
    
    Args:
        chunk: 整文化する文字起こしチャンク
        previous_result: 前のチャンクの処理結果
        background: 背景情報（オプション）
        model_name: 使用するAnthropicモデル名
    
    Returns:
        整文化されたテキスト
    """
    # Anthropicモデルの初期化
    llm = get_anthropic_client(model_name)
    
    # プロンプトテンプレートの作成
    template = create_prompt_template(with_context=True)
    prompt = ChatPromptTemplate.from_template(template)
    
    # 最新のLangChain APIを使用
    chain = prompt | llm
    result = chain.invoke({
        "chunk": chunk, 
        "previous_result": previous_result, 
        "background": background if background else ""
    })
    
    return result.content

def formalize_transcript(transcript: str, background: Optional[str] = None, model_name: str = "claude-3-7-sonnet-latest", max_tokens: int = 8000, overlap: int = 200) -> str:
    """
    文字起こしテキスト全体を整文化します。transcript_splitterを使用してテキストを分割し、
    文脈を維持しながら処理します。
    
    Args:
        transcript: 整文化する文字起こしテキスト全体
        background: 背景情報（オプション）
        model_name: 使用するAnthropicモデル名
        max_tokens: 各チャンクの最大トークン数
        overlap: チャンク間のオーバーラップトークン数
    
    Returns:
        整文化された完全なテキスト
    """
    # transcript_splitterを使用してテキストを分割
    chunks = split_transcript(transcript, max_tokens, overlap)
    print(f"テキストを {len(chunks)} チャンクに分割しました。")
    
    return formalize_chunks_with_context(chunks, background, model_name)

def formalize_chunks_with_context(chunks: List[str], background: Optional[str] = None, model_name: str = "claude-3-7-sonnet-latest") -> str:
    """
    複数の文字起こしチャンクを文脈を維持しながら整文化します。
    
    Args:
        chunks: 整文化する文字起こしチャンクのリスト
        background: 背景情報（オプション）
        model_name: 使用するAnthropicモデル名
    
    Returns:
        整文化された完全なテキスト
    """
    accumulated_result = ""
    
    for i, chunk in enumerate(chunks):
        print(f"チャンク {i+1}/{len(chunks)} を処理中...")
        
        if i == 0:
            # 最初のチャンクは通常の方法で処理
            accumulated_result = formalize_chunk(chunk, background, model_name)
        else:
            # 2つ目以降のチャンクは前の結果を考慮して処理
            next_part = formalize_with_context(chunk, accumulated_result, background, model_name)
            # 自然な接続のために単純に連結（改行を減らす）
            accumulated_result = accumulated_result + "\n" + next_part
    
    return accumulated_result

def generate_questions(transcript: str, model_name: str = "claude-3-7-sonnet-latest") -> str:
    """
    文字起こしテキストを分析し、文脈理解のための疑問点を生成します。
    
    Args:
        transcript: 分析する文字起こしテキスト
        model_name: 使用するAnthropicモデル名
    
    Returns:
        生成された疑問点のリスト（マークダウン形式）
    """
    # Anthropicモデルの初期化
    llm = get_anthropic_client(model_name)
    
    # プロンプトテンプレートの作成
    template = """
    <system_role>
    あなたは文字起こしテキストを分析し、文脈理解のために必要な疑問点を抽出するプロフェッショナルです。
    以下の文字起こしテキストを読み、文脈を理解する上で不明確な点や背景情報が必要な点について、
    5〜10個程度の具体的な疑問を生成してください。
    </system_role>

    <input_transcript>
    {transcript}
    </input_transcript>
    
    <processing_instructions>
    - テキストの内容を深く理解するために必要な疑問点を抽出してください
    - 専門用語や略語の意味に関する疑問を含めてください
    - 話者の関係性や立場に関する疑問を含めてください
    - 議論されているプロジェクトや事象の背景に関する疑問を含めてください
    - 時系列や因果関係が不明確な部分に関する疑問を含めてください
    - 具体的で明確な質問を作成してください
    - 質問は箇条書きでマークダウン形式で出力してください
    - 各質問の重要度や優先度に応じて並べ替えてください
    </processing_instructions>
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    
    # 最新のLangChain APIを使用
    chain = prompt | llm
    result = chain.invoke({"transcript": transcript})
    
    return result.content
