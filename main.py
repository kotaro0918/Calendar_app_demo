import streamlit as st
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os
import dateutil.parser
import datetime

# カレンダーAPIのスコープを設定
SCOPES = ['https://www.googleapis.com/auth/calendar']
creds = None
# タイトル
st.title('Calendar app Demo')

ID_list = ["aivalix.calendar.app.dev@gmail.com", "big.i.land.k@gmail.com"]

user1 = None
user2 = None
term = None
# Expanderの作成
with st.expander("誰の予定が空いてるか選択してください"):
    # ユーザーに選択させるオプション
    user1 = st.selectbox(
        'メールアドレスを選択してください:',
        (ID_list[0], ID_list[1]),
        key = "user1_select"
    )
# Expanderの作成
with st.expander("誰の予定が空いてるか選択してください"):
    # ユーザーに選択させるオプション
    user2 = st.selectbox(
        'メールアドレスを選択してください:',
        (ID_list[0], ID_list[1]),
        key = "user2_select"
    )
with st.expander("今後何週間の予定を調べるか選択してください"):
    # ユーザーに選択させるオプション
    option = st.selectbox(
        '好きな数字を選んでください:',
        ('1', '2', '3', '4')
    )
term = int(option) * 7

#午前7時から午後8時までの間で空いている時間帯を抽出します
def find_free_time(date,ID):
    # 指定日と時間帯の設定
    date = date
    start_time = date + 'T07:00:00+09:00'  # JSTで午前7時
    end_time = date + 'T20:00:00+09:00'    # JSTで午後8時
    # APIを使用して指定日のイベントを取得
    events_result = service.events().list(
        calendarId=ID,
        timeMin=start_time,
        timeMax=end_time,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    # 予定のない時間帯を探す
    free_time_blocks = [(start_time, end_time)]

    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        new_free_time_blocks = []
        for free_start, free_end in free_time_blocks:
            if start <= free_start and end >= free_end:
                # イベントが空き時間全体を覆っている場合、空き時間を削除
                continue
            elif start <= free_start < end <= free_end:
                # イベントが空き時間の始まりの一部を覆っている場合
                new_free_time_blocks.append((end, free_end))
            elif free_start < start <= free_end <= end:
                # イベントが空き時間の終わりの一部を覆っている場合
                new_free_time_blocks.append((free_start, start))
            elif start > free_start and end < free_end:
                # イベントが空き時間の中間にある場合、空き時間を2つに分割
                new_free_time_blocks.append((free_start, start))
                new_free_time_blocks.append((end, free_end))
            else:
                # イベントが空き時間に影響を与えない場合
                new_free_time_blocks.append((free_start, free_end))
        free_time_blocks = new_free_time_blocks
    return(free_time_blocks)

def find_common_free_time(date, calendar1_id, calendar2_id):
    # それぞれのカレンダーで空いている時間帯を見つける
    free_times_1 = find_free_time(date, calendar1_id)
    free_times_2 = find_free_time(date, calendar2_id)

    # 共通の空いている時間帯を見つける
    common_free_times = []
    for start1, end1 in free_times_1:
        for start2, end2 in free_times_2:
            # 共通の開始時間と終了時間を見つける
            common_start = max(start1, start2)
            common_end = min(end1, end2)
            # 共通の時間帯が存在する場合（開始時間が終了時間より前の場合）
            if common_start < common_end:
                common_free_times.append((common_start, common_end))

    return(common_free_times)


if st.button('空き時間を探します'):
    # トークンファイルが存在する場合、トークンを読み込む
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # トークンが無効な場合は、ユーザー認証フローを実行
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # 新しいトークンを保存
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    service = build('calendar', 'v3', credentials=creds)

    from datetime import datetime, timedelta

    # 現在の日付と時刻
    now = datetime.now()

    # 今日を含む今から1週間の日付を出力
    dates = [(now + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(term)]
    for date in dates:
        result = find_common_free_time(str(date),user1,user2)
        st.write("予定のない時間帯:")
        for common_start, common_end in result:
            st.write(f"開始: {common_start}, 終了: {common_end}")



name = st.text_input("イベントの名前を指定してください")
location = st.text_input("場所を指定してください、オンラインの時はオンライン")
description = st.text_input("イベントの概要")
date = st.text_input("イベントの日にち、04-05のフォーマットで入力してください")
start = st.text_input("スタート時間,08:30:00のフォーマットで入力してください")
end  = st.text_input("終了時間,08:30:00のフォーマットで入力してください")

start = "2024-" +date + "T" + start +"+09:00"
end = "2024-" +date + "T" + end +"+09:00"
# イベントデータを作成
def make_event(name,location,description,start,end):
    event = {
        'summary': name,
        'location': location,
        'description': description,
        'start': {
            'dateTime': start,
        },
        'end': {
            'dateTime': end
        },
    }
    return(event)
# ボタンがクリックされた時の処理
if st.button('カレンダーに予定を作成'):
    # トークンファイルが存在する場合、トークンを読み込む
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # トークンが無効な場合は、ユーザー認証フローを実行
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # 新しいトークンを保存
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    service = build('calendar', 'v3', credentials=creds)
    # イベントを追加
    event = make_event(name,location,description,start,end)
    created_event = service.events().insert(calendarId='primary', body=event).execute()
    # 処理が完了したことを示すフラグをセッション状態に追加
    st.session_state['processing_complete'] = True

# 処理が完了した後に実行する処理
if 'processing_complete' in st.session_state and st.session_state['processing_complete']:
    st.write('Event created: %s' % (created_event.get('htmlLink')))