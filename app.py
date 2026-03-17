import streamlit as st
from utils.goodnoteHelper import convert_goodnotes_to_mp3
import os

st.title('GoodNotes To MP3')

goodnote_file = st.file_uploader("Upload a .goodnotes file", type=["goodnotes"])

# 1. Run 버튼을 눌렀을 때의 동작
if goodnote_file:
    if st.button("Run"):
        with st.spinner("Converting... Please wait."):
            # utils 함수 실행
            output_dir = convert_goodnotes_to_mp3(goodnote_file)
            
            # 주의: utils 함수가 반환하는 값에 따라 이름이 다를 수 있습니다.
            # 기존 사용자님 코드에 맞춰 ".zip"을 붙였습니다.
            zip_file_path = output_dir + ".zip" 
            
            # 파일이 정상적으로 만들어졌는지 확인
            if os.path.exists(zip_file_path):
                # 파일을 하드디스크가 아닌 '메모리'로 읽어오기
                with open(zip_file_path, "rb") as file:
                    st.session_state['zip_data'] = file.read()
                    st.session_state['zip_name'] = goodnote_file.name.replace(".goodnotes", ".zip")
                
                # 메모리에 저장했으니 서버 용량 확보를 위해 원본 파일은 즉시 삭제
                os.remove(zip_file_path)
                st.success("Convert Complete! You can download the file below.")
            else:
                st.error("Error: Could not find the converted .zip file.")

else:
    # 파일이 안 올라왔을 때는 Run 버튼 대신 안내문구 띄우기 (옵션)
    st.info("Please upload a .goodnotes file to start.")

# 2. 다운로드 버튼은 반드시 Run 버튼의 바깥(독립된 공간)에 있어야 합니다!
# 메모리(session_state)에 데이터가 존재할 때만 다운로드 버튼 표시
if 'zip_data' in st.session_state:
    st.download_button(
        label="Download mp3 files",
        data=st.session_state['zip_data'],
        file_name=st.session_state['zip_name'],
        mime="application/zip"
    )
