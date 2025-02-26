from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re

def split_transcript(text: str, max_tokens: int = 3000, overlap: int = 0) -> List[str]:
    """
    文字起こしテキストを適切なサイズのチャンクに分割します。
    タイムスタンプや話者の切り替わりを優先して分割します。
    
    Args:
        text: 分割する文字起こしテキスト
        max_tokens: 各チャンクの最大トークン数
        overlap: チャンク間のオーバーラップトークン数
    
    Returns:
        分割されたテキストチャンクのリスト
    """
    # テキストを前処理して、タイムスタンプや話者の切り替わりを強調
    # タイムスタンプのパターン（例：00:00）の前に改行を挿入
    processed_text = re.sub(r'(\d{2}:\d{2})', r'\n\n\1', text)
    
    # 話者の切り替わりを示すパターン（例：中村恒彦/ARS:）の前に改行を挿入
    processed_text = re.sub(r'([^:：\n]+[:：])', r'\n\n\1', processed_text)
    
    # 複数の連続した改行を2つの改行に統一
    processed_text = re.sub(r'\n{3,}', r'\n\n', processed_text)
    
    # タイムスタンプ、話者の切り替わり、段落の区切りを優先して分割
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_tokens,
        chunk_overlap=overlap,
        length_function=len,
        separators=[
            "\n\n",    # 2つの改行（タイムスタンプや話者の切り替わり）
            "\n",      # 1つの改行
            ". ",      # 文の区切り
            "。",      # 日本語の文の区切り
            "、",      # 読点
            " ",       # スペース
            ""         # 文字単位
        ]
    )
    
    chunks = text_splitter.split_text(processed_text)
    
    # 各チャンクの先頭にタイムスタンプがない場合、前のチャンクから最後のタイムスタンプを取得して追加
    for i in range(1, len(chunks)):
        if not re.match(r'^\d{2}:\d{2}', chunks[i].strip()):
            # 前のチャンクから最後のタイムスタンプを検索
            last_timestamp = re.findall(r'(\d{2}:\d{2})', chunks[i-1])
            if last_timestamp:
                # 最後のタイムスタンプを現在のチャンクの先頭に追加
                chunks[i] = f"{last_timestamp[-1]} (続き) " + chunks[i]
    
    return chunks 