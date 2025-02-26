import streamlit as st
import os
from article_generator import (
    validate_api_key, set_api_key, 
    formalize_chunk, formalize_with_context,
    split_transcript
)

def main():
    st.set_page_config(page_title="文字起こし整文化ツール", page_icon="📝", layout="wide")
    
    st.title("文字起こしテキストの整文化")
    st.markdown("文字起こしテキストを読みやすく整理された会話の発言録に変換するツールです。")
    
    # 環境変数からAPIキーを取得
    env_api_key = os.environ.get("ANTHROPIC_API_KEY")
    if env_api_key and validate_api_key(env_api_key):
        set_api_key(env_api_key)
    
    # サイドバーにAPIキー入力欄とモデル選択を設置
    with st.sidebar:
        st.header("設定")
        
        # APIキーの状態を表示
        if env_api_key and validate_api_key(env_api_key):
            st.success("環境変数からAPIキーが読み込まれました")
            api_key_placeholder = "環境変数から読み込み済み"
        else:
            api_key_placeholder = ""
        
        api_key = st.text_input(
            "Anthropic APIキー", 
            type="password", 
            help="Anthropic APIキーを入力してください。環境変数ANTHROPIC_API_KEYが設定されている場合は自動的に使用されます。",
            placeholder=api_key_placeholder
        )
        
        # 手動入力されたAPIキーの検証
        if api_key:
            if validate_api_key(api_key):
                set_api_key(api_key)
                st.success("APIキーが設定されました")
            else:
                st.error("APIキーの形式が正しくありません")
        
        # モデル選択ドロップダウン
        model_options = {
            "claude-3-7-sonnet-latest": "Claude 3.7 Sonnet (推奨)",
            "claude-3-5-sonnet-latest": "Claude 3.5 Sonnet",
            "claude-3-opus-latest": "Claude 3 Opus",
            "claude-3-haiku-latest": "Claude 3 Haiku (高速・低コスト)"
        }
        selected_model = st.selectbox(
            "使用するモデル",
            options=list(model_options.keys()),
            format_func=lambda x: model_options[x],
            help="整文化に使用するAnthropicのモデルを選択してください"
        )
        
        # モデル情報の表示
        model_info = {
            "claude-3-7-sonnet-latest": "最新の高性能モデル。バランスの取れた性能と速度を提供します。",
            "claude-3-5-sonnet-latest": "高性能なモデルで、多くのタスクに適しています。",
            "claude-3-opus-latest": "最も高性能なモデルですが、処理に時間がかかります。",
            "claude-3-haiku-latest": "軽量で高速なモデルです。シンプルなタスクに適しています。"
        }
        st.info(model_info[selected_model])
        
        st.markdown("---")
        st.markdown("このツールはLangChainとAnthropic Claudeを使用しています。")
    
    # メイン画面の入力フォーム
    with st.form("formalize_form"):
        # 文字起こしテキスト入力
        transcript = st.text_area("文字起こしテキスト", height=300, 
                                help="整文化したい文字起こしテキストを入力してください")
        
        # 背景情報入力
        background = st.text_area("背景情報（任意）", height=100, 
                                help="文字起こしの理解に役立つ背景知識や補足情報を入力してください")
        
        # 実行ボタン
        submit_button = st.form_submit_button("整文化する")
    
    # 整文化処理
    if submit_button:
        if not transcript:
            st.error("文字起こしテキストを入力してください")
            return
        
        if not validate_api_key():
            st.error("APIキーが設定されていません。サイドバーでAPIキーを入力するか、環境変数ANTHROPIC_API_KEYを設定してください")
            return
        
        try:
            with st.spinner("整文化処理中..."):
                # 進捗表示用のコンテナ
                progress_container = st.container()
                
                # チャンク分割の前処理
                chunks = split_transcript(transcript)
                total_chunks = len(chunks)
                
                with progress_container:
                    st.write(f"テキストを {total_chunks} チャンクに分割しました。")
                    st.write(f"使用モデル: {model_options[selected_model]}")
                    progress_text = st.empty()
                    progress_bar = st.progress(0)
                
                # 進捗状況を更新するコールバック関数
                def update_progress(current_chunk, total_chunks):
                    progress = current_chunk / total_chunks
                    progress_text.write(f"チャンク {current_chunk}/{total_chunks} を処理中...")
                    progress_bar.progress(progress)
                
                # カスタムコールバック関数を使用して整文化を実行
                formalized_text = process_with_progress(chunks, background, update_progress, selected_model)
                
                # 進捗表示を完了に
                progress_bar.progress(1.0)
                progress_text.write("処理が完了しました！")
            
            # 結果表示
            st.success("整文化が完了しました！")
            st.markdown("## 整文化されたテキスト")
            st.markdown(formalized_text)
            
            # ダウンロードボタン
            st.download_button(
                label="整文化テキストをダウンロード",
                data=formalized_text,
                file_name="formalized_transcript.md",
                mime="text/markdown"
            )
        
        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")

def process_with_progress(chunks, background, progress_callback, model_name="claude-3-7-sonnet-latest"):
    """
    進捗状況を表示しながらチャンクを処理します。
    
    Args:
        chunks: 処理するチャンクのリスト
        background: 背景情報
        progress_callback: 進捗状況を更新するコールバック関数
        model_name: 使用するモデル名
    
    Returns:
        整文化されたテキスト
    """
    accumulated_result = ""
    total_chunks = len(chunks)
    
    for i, chunk in enumerate(chunks):
        # 進捗状況を更新
        progress_callback(i + 1, total_chunks)
        
        if i == 0:
            # 最初のチャンクは通常の方法で処理
            accumulated_result = formalize_chunk(chunk, background, model_name)
        else:
            # 2つ目以降のチャンクは前の結果を考慮して処理
            next_part = formalize_with_context(chunk, accumulated_result, background, model_name)
            # チャンク間にMarkdownのセパレーターを追加
            accumulated_result = accumulated_result + "\n\n----\n\n" + next_part
    
    return accumulated_result

if __name__ == "__main__":
    main() 