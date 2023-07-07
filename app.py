import streamlit as st
import pandas as pd
import numpy as np
import json
import openai
import time

# Streamlit Community Cloudの「Secrets」からOpenAI API keyを取得
openai.api_key = st.secrets.OpenAIAPI.openai_api_key

# スコアリング基準
criteria_dict = {'◎': 4, '◯': 2, '△': 1, '✕': 0}

# サイドバーに入力ウィジェットを移動
sidebar = st.sidebar

# Title入力
title = sidebar.text_input('Title', 'こどもの好きなメニュー')

st.sidebar.markdown('---')

def reset_text_inputs():
	# セッションステートを更新
	for i in range(4):
		st.session_state[f'オプション{i+1}'] = ""
		st.session_state[f'軸{i+1}'] = ""

	# ページをリロードしてテキスト入力ウィジェットをクリア
	st.experimental_rerun()

# オプションと軸をクリアするためのボタン
if st.sidebar.button('オプションと軸を全てクリア'):
	reset_text_inputs()

# オプション入力
default_options = ["ハンバーグ", "ピザ", "オムライス", "パスタ"]
options_list = [sidebar.text_input(f'オプション{i+1}', value=st.session_state.get(f'オプション{i+1}', default_options[i])) for i in range(4)]

# 軸入力
default_axes = ["簡単さ", "おいしさ", "栄養バランス", "見た目"]
axes_list = [sidebar.text_input(f'軸{i+1}', value=st.session_state.get(f'軸{i+1}', default_axes[i])) for i in range(4)]

# 入力フィールドの値をセッションステートに保存
for i in range(4):
	st.session_state[f'オプション{i+1}'] = options_list[i]
	st.session_state[f'軸{i+1}'] = axes_list[i]


# 空のオプションと軸を除外
options_list = [option for option in options_list if option]
axes_list = [ax for ax in axes_list if ax]

# メインの表示エリアにTitleをh1スタイルで表示

st.markdown(f"# 「{title}」のオプション評価")



## オプションと軸をクリアするためのボタン
#if st.button('オプションと軸を全てクリア'):
#	reset_text_inputs()
	
for i in range(4):
	# セッションステートのキーが存在するかチェックし、存在しない場合は初期化する
	if f'オプション{i+1}' not in st.session_state:
		st.session_state[f'オプション{i+1}'] = ""
	if f'軸{i+1}' not in st.session_state:
		st.session_state[f'軸{i+1}'] = ""

	# 一時的な値 "temp" がセットされていたら空文字列に戻す
	if st.session_state[f'オプション{i+1}'] == "temp":
		st.session_state[f'オプション{i+1}'] = ""
	if st.session_state[f'軸{i+1}'] == "temp":
		st.session_state[f'軸{i+1}'] = ""


# 表の表示エリア
#st.write('選択肢評価')


if options_list and axes_list:

	# 評価表の初期化
	table = pd.DataFrame(index=options_list, columns=axes_list, dtype=object)

	# 一時的な評価値保存用辞書
	ratings_dict = {}

	# 評価入力と集計
	for option in options_list:
		cols = st.columns(len(axes_list))
		for i, ax in enumerate(axes_list):
			rating = cols[i].selectbox(f'{option} - {ax}', list(criteria_dict.keys()), key=f'{option}{ax}')
			table.loc[option, ax] = rating
			# 評価値を辞書に保存
			ratings_dict[(option, ax)] = rating

	# 各選択肢のスコア計算
	scores = {option: sum(criteria_dict[ratings_dict.get((option, ax), 0)] for ax in axes_list) for option in options_list}
	table['点数'] = pd.Series(scores)

	st.write(table)

else:
	st.warning("オプションと軸をそれぞれ1つ以上入力してください。")

# Function calling using OpenAI's ChatCompletion API
def get_options_and_axes_from_gpt3(title):
	# Send a chat message to GPT-3 to brainstorm options and axes
	response = openai.ChatCompletion.create(
		model="gpt-3.5-turbo-0613",
		messages=[
			{"role": "system", "content": "あなたは指定形式のフォーマッターです。指定形式のみを出力します。"},
			{"role": "user", "content": f'あなたはタイトルを元に、選択肢評価をするためのブレストをしてください。\nその内容を元に、オプション4つと軸を4つ、カンマ区切りで表示してください。\nタイトルは"{title}"です。\n作成する形式の例は次のとおりです。\n\n[オプションの例]:ハンバーガー,ピザ, オムライス, パスタ\n[軸の例]:簡単さ,おいしさ,栄養バランス,見た目の楽しさ\n\nオプションの例と軸の例の間は改行してください。この形式以外は絶対に何があっても出力しないでください。'},
		]
	)

	# Extract the content from the response
	content = response['choices'][0]['message']['content']
	#st.write(f"Debug: {content}")  # デバッグ用の出力
	return content

# Add a placeholder where the GPT-3 output will be displayed
gpt3_output_placeholder = st.empty()

def parse_generated_content(content):
	# Extract options and axes from the content
	options_line, axes_line = content.split('\n')

	# Remove the leading label and split by commas
	options = options_line.replace('[オプションの例]:', '').split(',')
	axes = axes_line.replace('[軸の例]:', '').split(',')

	# Remove leading/trailing spaces
	options = [option.strip() for option in options]
	axes = [ax.strip() for ax in axes]

	return options, axes

if title:
	# Initialize the session state for generated content
	if 'generated_content' not in st.session_state:
		st.session_state.generated_content = ""
		
	st.markdown('---')


	st.markdown(f"## Title「{title}」から、AIでオプションと軸を作成する")
	generating = st.button('作成！')

	if generating:
		with st.spinner('オプションと軸の案を作成中...'):
			st.session_state.generated_content = get_options_and_axes_from_gpt3(title)

	if st.session_state.generated_content:
		options, axes = parse_generated_content(st.session_state.generated_content)


	# AIが提案したオプションと軸を表示
	if st.session_state.generated_content:
		options, axes = parse_generated_content(st.session_state.generated_content)

		# 各オプションと軸に設定するボタン
		# 各オプションと軸に設定するボタン
		for i, option in enumerate(options[:4]):
			if st.button(f'オプション{i+1}に「{option}」を設定'):
				st.session_state[f'オプション{i+1}'] = option
				st.experimental_rerun()

		for i, ax in enumerate(axes[:4]):
			if st.button(f'軸{i+1}に「{ax}」を設定'):
				st.session_state[f'軸{i+1}'] = ax
				st.experimental_rerun()

		# 全てを設定するボタン
		if st.button('全てを設定'):
			for i, option in enumerate(options[:4]):
				st.session_state[f'オプション{i+1}'] = option
			for i, ax in enumerate(axes[:4]):
				st.session_state[f'軸{i+1}'] = ax
			st.experimental_rerun()


	# ボタンの状態に基づいてテキストフィールドを更新
	for i in range(1, 5):
		if st.session_state.get(f'option_button_{i}', False):
			st.session_state[f'オプション{i}'] = options[i-1]
			st.session_state[f'option_button_{i}'] = False  # ボタンの状態をリセット
		if st.session_state.get(f'axis_button_{i}', False):
			st.session_state[f'軸{i}'] = axes[i-1]
			st.session_state[f'axis_button_{i}'] = False  # ボタンの状態をリセット
		if st.session_state.get('set_all_button', False):
			st.session_state[f'オプション{i}'] = options[i-1]
			st.session_state[f'軸{i}'] = axes[i-1]
	if st.session_state.get('set_all_button', False):
		st.session_state['set_all_button'] = False  # ボタンの状態をリセット

