from typing import List, Optional
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
    
    会話の例：
    **Aさん** : 内容~
    
    **Bさん** : 内容~
    </system_role>

    <background_info>
    {background}
    </background_info>
    """
    
    if with_context:
        base_template += """
    <previous_content>
    {previous_result}
    </previous_content>
    
    <input_transcript>
    {chunk}
    </input_transcript>
    
    <processing_instructions>
    - 前のチャンクの処理結果との一貫性を保ちながら、新しいチャンクを整う化してください
    - 前のチャンクで既に言及された内容との重複を避けてください
    - 話者の名前や役職などの表記は前のチャンクと統一してください
    - 話の流れが自然につながるようにしてください
    - 文字起こしの内容をできる限り正確に保持してください
    - 話し言葉を自然な書き言葉に変換してください
    - 冗長な表現や繰り返しを整理してください
    - 文脈を保ちながら、論理的で読みやすい段落構成にしてください
    - 背景情報を活用して、文脈や専門用語の理解を深めてください
    - 不明瞭な表現は背景情報を参考に明確にしてください
    - 原文の意図や主張を変えないでください
    - 内容を追加せず、与えられた情報のみを使用してください
    - 見出しは作成せず、会話の流れをそのまま表現してください
    - 「# 〜」のような見出しは決して作成しないでください
    - 話者分離が正確ではない可能性があります。文脈から話者が違う場合は修正を提案してください
    - 前のチャンクとの接続部分が自然になるようにしてください
    - 「以下の文字起こしを整理された会話の発言録に書き直しました：」のような前置きをせず、発言録のみを出力してください。
    </processing_instructions>
    """
    else:
        base_template += """
    <input_transcript>
    {chunk}
    </input_transcript>
    
    <processing_instructions>
    - 文字起こしの内容をできる限り正確に保持してください
    - 話し言葉を自然な書き言葉に変換してください
    - 冗長な表現や繰り返しを整理してください
    - 文脈を保ちながら、論理的で読みやすい段落構成にしてください
    - 背景情報を活用して、文脈や専門用語の理解を深めてください
    - 不明瞭な表現は背景情報を参考に明確にしてください
    - 原文の意図や主張を変えないでください
    - 内容を追加せず、与えられた情報のみを使用してください
    - 見出しは作成せず、会話の流れをそのまま表現してください
    - 「# 〜」のような見出しは使用しないでください
    </processing_instructions>
    """
    
    return base_template

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
    llm = ChatAnthropic(model=model_name)
    
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
    llm = ChatAnthropic(model=model_name)
    
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
    llm = ChatAnthropic(model=model_name)
    
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
