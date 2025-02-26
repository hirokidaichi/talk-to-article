from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re

def split_transcript(text: str, max_tokens: int = 3000, overlap: int = 0) -> List[str]:
    """
    文字起こしテキストを適切なサイズのチャンクに分割します。
    段落や自然な区切りを優先して分割します。
    
    Args:
        text: 分割する文字起こしテキスト
        max_tokens: 各チャンクの最大トークン数
        overlap: チャンク間のオーバーラップトークン数
    
    Returns:
        分割されたテキストチャンクのリスト
    """
    # 複数の改行を含むパターンを最優先で区切りとして使用
    # 次に段落の区切り、文の区切りの順で試行
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_tokens,
        chunk_overlap=overlap,
        length_function=len,
        separators=[
            "\n\n\n",  # 3つの改行
            "\n\n",    # 2つの改行（段落区切り）
            "\n",      # 1つの改行
        ]
    )
    
    # テキストを前処理して、自然な区切りを強調
    # 話者の切り替わりなどで2つ以上の改行を挿入
    processed_text = re.sub(r'(\*\*[^*]+\*\*\s*[:：])', r'\n\n\1', text)
    
    chunks = text_splitter.split_text(processed_text)
    return chunks 