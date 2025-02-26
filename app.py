import streamlit as st
from article_generator import (
    validate_api_key, set_api_key, 
    formalize_chunk, formalize_with_context,
    split_transcript, generate_questions,
    get_api_key_from_local_storage, save_api_key_to_local_storage,
    get_api_key
)

def main():
    st.set_page_config(page_title="文字起こし整文化ツール", page_icon="📝", layout="wide")
    
    st.title("文字起こしテキストの整文化")
    st.markdown("文字起こしテキストを読みやすく整理された会話の発言録に変換するツールです。")
    
    # ローカルストレージからAPIキーを取得
    local_api_key = get_api_key_from_local_storage()
    
    # ローカルストレージからAPIキーを設定
    if local_api_key and validate_api_key(local_api_key):
        set_api_key(local_api_key)
    
    # サイドバーにAPIキー入力欄とモデル選択を設置
    with st.sidebar:
        st.header("設定")
        
        # APIキーの状態を表示
        current_api_key = get_api_key()
        if current_api_key and validate_api_key(current_api_key):
            st.success("APIキーが設定されています")
            api_key_placeholder = "APIキー設定済み"
        else:
            api_key_placeholder = ""
        
        # APIキー入力欄
        api_key = st.text_input(
            "Anthropic APIキー", 
            type="password", 
            help="Anthropic APIキーを入力してください。ブラウザに保存することもできます。",
            placeholder=api_key_placeholder
        )
        
        # APIキーをブラウザに保存するチェックボックス
        save_to_browser = st.checkbox("APIキーをブラウザに保存する", 
                                     help="APIキーをブラウザのローカルストレージに保存します。次回アクセス時に自動的に読み込まれます。")
        
        # 手動入力されたAPIキーの検証
        if api_key:
            if validate_api_key(api_key):
                set_api_key(api_key)
                st.success("APIキーが設定されました")
                
                # ブラウザに保存するオプションが選択されている場合
                if save_to_browser:
                    if save_api_key_to_local_storage(api_key):
                        st.success("APIキーがブラウザに保存されました")
                    else:
                        st.error("APIキーのブラウザへの保存に失敗しました")
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
    

    # メイン画面の入力部分
    transcript = st.text_area("文字起こしテキスト", height=300, 
                    help="整文化したい文字起こしテキストを入力してください")
    
    # 疑問点生成ボタン
    if st.button("文脈理解のための疑問点を生成"):
        if not get_api_key():
            st.error("APIキーが設定されていません。サイドバーでAPIキーを入力してください")
        else:
            try:
                with st.spinner("疑問点を生成中..."):
                    # 疑問点を生成
                    questions = generate_questions(transcript, selected_model)
                    st.success("疑問点の生成が完了しました！")
                    st.markdown(questions)
                
            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")

    # 背景情報入力
    background = st.text_area("背景情報（任意）", height=100, 
                            help="文字起こしの理解に役立つ背景知識や補足情報を入力してください")
    
    # 整文化ボタン
    formalize_button = st.button("整文化する")
    
    # 進捗表示用のコンテナ
    progress_container = st.container()
    
    # 結果表示用のコンテナ
    result_container = st.container()
    
    
    # 整文化処理
    if formalize_button:
        if not transcript:
            st.error("文字起こしテキストを入力してください")
            return
        
        if not get_api_key():
            st.error("APIキーが設定されていません。サイドバーでAPIキーを入力してください")
            return
        
        try:
            
            with st.spinner("整文化処理中..."):
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
            with result_container:
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
    直前3つのチャンクの処理結果をコンテキストとして使用します。
    
    Args:
        chunks: 処理するチャンクのリスト
        background: 背景情報
        progress_callback: 進捗状況を更新するコールバック関数
        model_name: 使用するモデル名
    
    Returns:
        整文化されたテキスト
    """
    # 処理結果を保存するリスト
    processed_chunks = []
    total_chunks = len(chunks)
    
    for i, chunk in enumerate(chunks):
        # 進捗状況を更新
        progress_callback(i + 1, total_chunks)
        
        if i == 0:
            # 最初のチャンクは通常の方法で処理
            result = formalize_chunk(chunk, background, model_name)
            processed_chunks.append(result)
        else:
            # 直前3つのチャンクの処理結果を取得
            context_window = 3
            start_idx = max(0, i - context_window)
            recent_results = processed_chunks[start_idx:i]
            
            # 直前のチャンクの処理結果を連結してコンテキストとして使用
            context = "\n\n".join(recent_results)
            
            # コンテキストを考慮して処理
            next_part = formalize_with_context(chunk, context, background, model_name)
            processed_chunks.append(next_part)
    
    # 全ての処理結果を連結
    return "\n\n----\n\n".join(processed_chunks)

if __name__ == "__main__":
    main() 