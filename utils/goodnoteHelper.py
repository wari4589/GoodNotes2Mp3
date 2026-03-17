import os
from typing import List
import subprocess
from tempfile import NamedTemporaryFile
import streamlit as st
import shutil
from concurrent.futures import ThreadPoolExecutor # ray 대신 파이썬 기본 병렬처리 모듈 사용


def convert_goodnotes_to_mp3(goodnote_file, output_dir = None):
    """
    Convert goodnote file to MP3
    1. Goodnote -> Zip
    2. Zip -> MP4
    3. MP4 -> MP3
    """
    with NamedTemporaryFile(dir='.', suffix='.zip') as f:
        with st.status("Converting to mp3...", expanded=True) as status:
            f.write(goodnote_file.getbuffer())
            if output_dir:
                output_dir = os.path.join(output_dir.strip(), goodnote_file.name.replace(".goodnotes", ""))
            else:
                output_dir = os.path.join(os.path.dirname(f.name),
                                            goodnote_file.name.replace(".goodnotes", ""))

            os.makedirs(output_dir, exist_ok=True)
            shutil.unpack_archive(f.name, output_dir)

            mp4_folder = os.path.join(output_dir, 'attachments')
            mp4_files = [os.path.join(mp4_folder, f) for f in os.listdir(mp4_folder)]

            for i, mp4_file in enumerate(mp4_files):
                new_name = "Audio" + str(i + 1) + ".mp4"
                old_path = os.path.join(mp4_folder, mp4_file)
                new_path = os.path.join(mp4_folder, new_name)
                os.rename(old_path, new_path)

            # MP4 파일 리스트 가져오기
            mp4_files = [os.path.join(mp4_folder, f) for f in os.listdir(mp4_folder) if f.endswith('.mp4')]
            
            # --- 수정된 부분: ray 대신 파이썬 내장 라이브러리로 병렬 처리 ---
            # chunk를 나눌 필요 없이 ThreadPoolExecutor가 알아서 4개씩 동시에 작업해줍니다.
            with ThreadPoolExecutor(max_workers=4) as executor:
                executor.map(lambda mp4: _convert_to_mp3(mp4, output_dir), mp4_files)
            # -------------------------------------------------------------

            mp3_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir)
                        if f.endswith('.mp3')]
            
            for i, filename in enumerate(mp3_files):
                old_path = os.path.join(output_dir, filename)
                duration = _get_mp3_duration(old_path)
                new_name = f"Audio{i+1}" + duration + ".mp3"
                new_path = os.path.join(output_dir, new_name)
                os.rename(old_path, new_path)
                st.write("Complete: "+ new_name)
            
            _delete_non_mp3_files(output_dir)

            shutil.make_archive(goodnote_file.name.replace(".goodnotes", ""), "zip", output_dir)
            
            shutil.rmtree(output_dir)
            
            status.update(label="Convert Complete!", state="complete", expanded=True)

    return output_dir

# MP4 파일을 MP3로 변환하는 함수 (ray 관련 데코레이터 @ray.remote 삭제)
def _convert_to_mp3(mp4_file: str, output_dir: str):
    mp3_file_path = os.path.join(output_dir, os.path.splitext(os.path.basename(mp4_file))[0] + '.mp3')
    command = f'ffmpeg -i "{mp4_file}" -vn -acodec mp3 "{mp3_file_path}"'
    os.system(command)
    st.write("Complete")

def _get_mp3_duration(mp3_file_path):
    command = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', mp3_file_path]
    output = subprocess.check_output(command, universal_newlines=True)
    duration_seconds = float(output)
    return _format_duration(duration_seconds)

def _format_duration(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    return f"({minutes:02d}:{seconds:02d})"

def _delete_non_mp3_files(folder_path):
    for root, dirs, files in os.walk(folder_path, topdown=False):
        for file in files:
            if not file.endswith(".mp3"):
                file_path = os.path.join(root, file)
                os.remove(file_path)
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if not any(os.scandir(dir_path)):
                os.rmdir(dir_path)
