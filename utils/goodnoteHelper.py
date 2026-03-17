import os
import shutil
import subprocess
from tempfile import NamedTemporaryFile
from concurrent.futures import ThreadPoolExecutor
import streamlit as st

def _format_duration(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    return f"({minutes:02d}:{seconds:02d})"

def _get_mp3_duration(mp3_file_path):
    command = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', mp3_file_path]
    output = subprocess.check_output(command, universal_newlines=True)
    duration_seconds = float(output)
    return _format_duration(duration_seconds)

def _convert_to_mp3(mp4_file: str, output_dir: str):
    """단일 MP4 파일을 MP3로 변환"""
    mp3_file_path = os.path.join(output_dir, os.path.splitext(os.path.basename(mp4_file))[0] + '.mp3')
    command = f'ffmpeg -i "{mp4_file}" -vn -acodec mp3 "{mp3_file_path}" -y' # -y: 덮어쓰기
    subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) 
    return mp3_file_path

def _delete_non_mp3_files(folder_path):
    for root, dirs, files in os.walk(folder_path, topdown=False):
        for file in files:
            if not file.endswith(".mp3"):
                file_path = os.path.join(root, file)
                os.remove(file_path)
        for d in dirs:
            dir_path = os.path.join(root, d)
            if not any(os.scandir(dir_path)):
                os.rmdir(dir_path)

def convert_goodnotes_to_mp3(goodnote_file):
    """
    Goodnote -> Zip -> MP4 -> MP3 변환 메인 함수
    """
    with NamedTemporaryFile(dir='.', suffix='.zip', delete=False) as f:
        f.write(goodnote_file.getbuffer())
        temp_zip_path = f.name

    output_dir = os.path.join(".", goodnote_file.name.replace(".goodnotes", ""))
    os.makedirs(output_dir, exist_ok=True)

    with st.status("굿노트 파일을 변환하는 중입니다...", expanded=True) as status:
        st.write("1. 압축 해제 중...")
        shutil.unpack_archive(temp_zip_path, output_dir)
        os.remove(temp_zip_path) # 임시 zip 파일 삭제

        mp4_folder = os.path.join(output_dir, 'attachments')
        if not os.path.exists(mp4_folder):
            st.error("녹음 파일이 없는 굿노트 파일이거나 폴더 구조가 다릅니다.")
            return None

        st.write("2. 오디오 파일 추출 및 이름 변경 중...")
        mp4_files = [os.path.join(mp4_folder, file) for file in os.listdir(mp4_folder) if file.endswith('.mp4')]
        
        renamed_mp4_files = []
        for i, mp4_file in enumerate(mp4_files):
            new_name = f"Audio_{i + 1}.mp4"
            new_path = os.path.join(mp4_folder, new_name)
            os.rename(mp4_file, new_path)
            renamed_mp4_files.append(new_path)

        st.write("3. MP3로 변환 중 (조금만 기다려주세요)...")
        # ray 대신 파이썬 내장 스레드 풀 사용 (서버 터짐 방지를 위해 최대 2개씩 작업)
        with ThreadPoolExecutor(max_workers=2) as executor:
            mp3_paths = list(executor.map(lambda mp4: _convert_to_mp3(mp4, output_dir), renamed_mp4_files))

        st.write("4. 파일명에 길이(시간) 추가 중...")
        for i, old_mp3_path in enumerate(mp3_paths):
            if os.path.exists(old_mp3_path):
                duration = _get_mp3_duration(old_mp3_path)
                new_name = f"Audio_{i+1}_{duration}.mp3"
                new_path = os.path.join(output_dir, new_name)
                os.rename(old_mp3_path, new_path)
                st.write(f" - 완료: {new_name}")

        st.write("5. 마무리 정리 중...")
        _delete_non_mp3_files(output_dir)
        
        # 최종 결과물을 zip으로 압축
        final_zip_name = goodnote_file.name.replace(".goodnotes", "")
        shutil.make_archive(final_zip_name, "zip", output_dir)
        
        # 임시 작업 폴더 삭제
        shutil.rmtree(output_dir)
        
        status.update(label="변환이 완료되었습니다!", state="complete", expanded=False)

    return final_zip_name + ".zip"

# ----- 웹 UI 화면 구성 -----
st.set_page_config(page_title="Goodnotes Audio Extractor", page_icon="🎵")
st.title("Goodnotes to MP3 Converter")
st.write("굿노트 파일(.goodnotes)을 올리면 안에 있는 녹음 파일을 MP3로 변환해서 압축파일(.zip)로 돌려줍니다.")

uploaded_file = st.file_uploader("굿노트 파일을 올려주세요", type="goodnotes")

if uploaded_file is not None:
    if st.button("변환 시작", type="primary"):
        result_zip = convert_goodnotes_to_mp3(uploaded_file)
        if result_zip and os.path.exists(result_zip):
            with open(result_zip, "rb") as fp:
                st.download_button(
                    label="다운로드하기",
                    data=fp,
                    file_name=result_zip,
                    mime="application/zip"
                )
            os.remove(result_zip) # 다운로드 버튼 생성 후 서버 용량 확보를 위해 삭제
