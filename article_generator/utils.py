import os
from typing import Optional
import streamlit as st
from streamlit_local_storage import LocalStorage

def validate_api_key(api_key: Optional[str] = None) -> bool:
    """
    Anthropic APIキーの有効性を検証します。
    
    Args:
        api_key: 検証するAPIキー（オプション）
    
    Returns:
        APIキーが有効な形式かどうか
    """
    # 引数またはセッションステートからAPIキーを取得
    key = api_key
    
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
    Anthropic APIキーをセッションに設定します。
    
    Args:
        api_key: 設定するAPIキー
    """
    st.session_state.anthropic_api_key = api_key

def get_api_key() -> Optional[str]:
    """
    セッションからAPIキーを取得します。
    
    Returns:
        APIキー（存在する場合）
    """
    return st.session_state.get("anthropic_api_key")

def get_api_key_from_local_storage() -> Optional[str]:
    """
    ローカルストレージからAPIキーを取得します。
    
    Returns:
        APIキー（存在する場合）
    """
    try:
        local_storage = LocalStorage()
        api_key = local_storage.getItem("anthropic_api_key")
        return api_key
    except Exception:
        return None

def save_api_key_to_local_storage(api_key: str) -> bool:
    """
    APIキーをローカルストレージに保存します。
    
    Args:
        api_key: 保存するAPIキー
    
    Returns:
        保存が成功したかどうか
    """
    try:
        local_storage = LocalStorage()
        local_storage.setItem("anthropic_api_key", api_key)
        return True
    except Exception:
        return False

# 以下の関数は後方互換性のために残しておきます
def get_api_key_from_session() -> Optional[str]:
    """
    セッションステートからAPIキーを取得します。
    
    Returns:
        APIキー（存在する場合）
    """
    if "api_key" in st.session_state:
        return st.session_state.api_key
    return None

def save_api_key_to_session(api_key: str) -> None:
    """
    APIキーをセッションステートに保存します。
    
    Args:
        api_key: 保存するAPIキー
    """
    st.session_state.api_key = api_key 