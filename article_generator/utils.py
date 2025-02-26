import os
from typing import Optional

def validate_api_key(api_key: Optional[str] = None) -> bool:
    """
    Anthropic APIキーの有効性を検証します。
    
    Args:
        api_key: 検証するAPIキー（オプション）
    
    Returns:
        APIキーが有効な形式かどうか
    """
    # 環境変数からAPIキーを取得（api_keyが指定されていない場合）
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    
    # 簡易的な検証（実際のAPIキーの形式に合わせて調整）
    if not key:
        return False
    
    # Anthropicのキーは通常 "sk-" で始まる
    if not key.startswith("sk-"):
        return False
    
    # 最低限の長さチェック
    if len(key) < 20:
        return False
    
    return True

def set_api_key(api_key: str) -> None:
    """
    Anthropic APIキーを環境変数に設定します。
    
    Args:
        api_key: 設定するAPIキー
    """
    os.environ["ANTHROPIC_API_KEY"] = api_key 