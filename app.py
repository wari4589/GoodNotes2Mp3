import streamlit as st
from utils.goodnoteHelper import convert_goodnotes_to_mp3
import os

st.title('GoodNotes To MP3')

goodnote_file = st.file_uploader("Upload a .goodnotes file", type=["goodnotes"])

if goodnote_file:
    if st.button("Run"):
        with st.spinner("Converting... Please wait."):
            # 1. utils 함수 실행 (결과물 경로를 받아옵니다)
            result_path = convert_goodnotes_to_mp3(goodnote_file)
            
            # 2. 방어 코드: 반환된 이름 끝에 .zip이 없으면 붙여주고, 있으면 그대로 씁니다.
            # (이렇게 하면 utils 코드가 어떻게 생겼든 무조건 작동합니다!)
            if not result_path.endswith(".zip"):
                zip_file_path = result_path + ".zip"
            else:
                zip_file_path = result_path
            
            # 3. 파일이 정상적으로 만들어졌는지 최종 확인
            if os.path.exists(zip_file_path):
                # 파일을 메모리로 읽어오기
                with open(zip_file_path, "rb") as file:
                    st.session_state['zip_data'] = file.read()
                    st.session_state['zip_name'] = goodnote_file.name.replace(".goodnotes", ".zip")
                
                # 원본 파일 삭제 및 성공 메시지
                os.remove(zip_file_path)
                st.success("Convert Complete! You can download the file below.")
            else:
                # 만약 또 못 찾으면, 정확히 어떤 경로를 찾다 실패했는지 화면에 띄워줍니다.
                st.error(f"Error: Could not find the file at {zip_file_path}")

else:
    st.info("Please upload a .goodnotes file to start.")

# 4. 메모리에 데이터가 있을 때만 다운로드 버튼 표시
if 'zip_data' in st.session_state:
    st.download_button(
        label="Download mp3 files",
        data=st.session_state['zip_data'],
        file_name=st.session_state['zip_name'],
        mime="application/zip"
    )
