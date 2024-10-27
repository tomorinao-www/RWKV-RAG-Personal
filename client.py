import os
import asyncio
import re
import string
import random
from collections import OrderedDict

import streamlit as st
import pandas as pd

from src.utils.loader import Loader
from src.utils.internet import search_on_baike
from configuration import config as project_config
from src.services import sqlite_db, files_status_manager,llm_service_worker, index_service_worker




parent_dir = project_config.config.get('knowledge_base_path')
print(parent_dir)
default_knowledge_base_dir = os.path.join(parent_dir, "knowledge_data") # 默认联网知识的存储位置
if not os.path.exists(default_knowledge_base_dir):
    os.makedirs(default_knowledge_base_dir)

default_upload_knowledge_base_dir = os.path.join(default_knowledge_base_dir, "upload_knowledge")
if not os.path.exists(default_upload_knowledge_base_dir):
    os.makedirs(default_upload_knowledge_base_dir)




async def search_and_notify(search_query, output_dir, output_filename):
    # Run the async search function
    msg = await search_on_baike(search_query, output_dir, output_filename)
    return os.path.join(output_dir, output_filename), msg

def get_random_string(length):
    haracters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(haracters, k=length))


# 设置页面的全局CSS样式
def set_page_style():
    st.markdown(
        """
        <style>
        /* 调整侧边栏的样式 */
        .st-Sidebar {
            position: absolute; /* 绝对定位 */
            left: 0; /* 左侧对齐 */
            top: 0; /* 上侧对齐 */
            height: 100%; /* 占满整个视口高度 */
            padding: 20px; /* 内边距 */
            box-sizing: border-box; /* 边框计算在宽度内 */
        }
        /* 调整主内容区域的样式 */
        .st-App {
            margin-left: 250px; /* 为侧边栏留出空间 
            */
        }
        </style>
        """,
        unsafe_allow_html=True,
        # 禁用自动刷新
        # 这里设置成False
    )



def knowledgebase_manager():
    st.title("知识库管理")
    # 显示所有知识库
    collections = index_service_worker.show_collections({})
    if collections:
        st.subheader("知识库列表")
        collection_name_list = [i[0] for i in collections]
        collection_name_meta_data = [i[1] for i in collections]
        df = pd.DataFrame({'name': collection_name_list, 'meta_data': collection_name_meta_data})
        st.dataframe(df, use_container_width=True)
    else:
        collection_name_list = []
        st.warning("没有找到任何知识库。")

    st.subheader("新增知识库")
    new_collection_name = st.text_input("请输入新知识库的名称:")
    if st.button('添加'):
        if new_collection_name:
            collection_name_rule = r'^[a-zA-Z0-9][a-zA-Z0-9_]{1,31}[a-zA-Z0-9]$'
            if not re.match(collection_name_rule, new_collection_name):
                st.warning('知识库名称不合法,长度3-32的英文字符串')
            else:
                if new_collection_name in collection_name_list:
                    st.warning(f"知识库 '{new_collection_name}' 已经存在。")
                else:
                    try:
                        index_service_worker.create_collection({'collection_name': new_collection_name})
                        st.success(f"知识库 '{new_collection_name}' 已成功添加。")
                        collection_name_list.append(new_collection_name)
                    except Exception as e:
                        st.error(f"添加知识库时出错: {str(e)}")
        else:
            st.warning("请输入有效的知识库名称。")

    st.subheader("删除知识库")
    collection_to_delete = st.selectbox("选择要删除的知识库:", [''] + collection_name_list)
    if st.button('删除'):
        if collection_to_delete:
            try:
                index_service_worker.delete_collection({'collection_name': collection_to_delete})
                st.success(f"知识库 '{collection_to_delete}' 已成功删除。")
                if collection_name_list:
                    collection_name_list.remove(collection_to_delete)
            except Exception as e:
                st.error(f"删除知识库时出错: {str(e)}")
        else:
            st.warning("请选择一个知识库进行删除。")

    st.subheader("知识库详情")
    collection_to_detail = st.selectbox("选择知识库:",collection_name_list)
    if st.button('查看') and collection_to_detail:
        file_list = files_status_manager.get_collection_files(collection_to_detail)
        if file_list:
            st.write("文件列表:")
            df = pd.DataFrame({'文件': file_list, })
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("该知识库下没有找到任何文件。")


def internet_search():
    """
    知识入库
    """
    if 'internet_search_random_str' not in st.session_state or not st.session_state.internet_search_random_str:
        random_str = get_random_string(6)
        st.session_state.internet_search_random_str = random_str

    st.title("知识入库")
    st.subheader("联网搜索")
    st.markdown('<span style="font-size: 16px; color: blue;">❗ 通过关键词联网搜索知识！</span>', unsafe_allow_html=True)
    # 搜索查询输入
    search_query = st.text_input("请输入搜索关键词:", "", key="query_main")

    # 输出目录输入
    output_dir = st.text_input("请输入输出目录(:red[可更改]):", default_knowledge_base_dir, key="output_dir_main")

    # 输出文件名输入
    output_filename = st.text_input("请输入输出文件名(:red[可更改]):",
                                    "result_%s.txt" % st.session_state.internet_search_random_str,
                                    key="output_filename_main")

    # 按钮触发搜索并保存
    if st.button("搜索并保存"):
        if not search_query:
            st.error("请提供搜索关键词。")
        elif not output_dir:
            st.error("请提供输出目录。")
        else:
            try:
                if not output_filename:
                    output_filename = f'{search_query}.txt'
                filepath, msg = asyncio.run(search_and_notify(search_query, output_dir, output_filename))
                #st.session_state.internet_search_random_str = output_filename
                if not msg:
                    st.success(f"搜索结果已保存到: {filepath}")
                else:
                    st.warning(msg)
            except Exception as e:
                st.error(f"发生错误: {str(e)}")

    st.subheader("知识入库")
    st.markdown('<span style="font-size: 16px; color: blue;">❗可将上面的联网搜索的结果、手动输入文本、本地文件入库,入库前请确认左边正在使用的知识库是否正确 </span>', unsafe_allow_html=True)
    # 询问用户输入payload的方式
    input_method = st.selectbox(
        "请选择知识入库方式",
        ["服务端文件", "本地上传", "手动输入"],
        index=0
    )

    if input_method == "手动输入":
        payload_input = st.text_area("请输入要入库的内容（每条文本一行），然后Ctrl+Enter", height=300)
        load_button = st.button("分割文件")
        if payload_input and load_button:
            payload_texts = payload_input.split("\n")
            for idx, chunk in enumerate(payload_texts):
                tmp = [chunk]
                embeddings = llm_service_worker.get_embeddings({'texts': tmp, "bgem3_path": project_config.default_bgem3_path})
                result = index_service_worker.index_texts({"keys": None, "texts": tmp, "embeddings": embeddings, 'collection_name': st.session_state.kb_name})
                st.write(f"文本 {idx + 1}: {result}")
    elif input_method == "服务端文件":
        st.markdown(
            '<span style="font-size: 12px; color: blue;">❗服务端文件指该知识库文件在项目部署的服务器上,如果你知道这个文件在项目部署的服务器上位置,'
            '填写到输入知识库路径输入框 </span>',
            unsafe_allow_html=True)

        input_path = st.text_input("请输入知识库路径:", key="input_path_key")
        chunk_size = st.number_input("请输入块大小（字符数）:", min_value=1, value=512, key="chunk_size_key")
        chunk_overlap = st.number_input("请输入块重叠（字符数）:", min_value=0, value=0, key="chunk_overlap_key")
        output_path = st.text_input("请输入输出目录路径(:red[可更改]):",default_knowledge_base_dir, key="output_path_key")

        # 加载按钮
        load_button = st.button("加载并分割文件")
        if load_button and input_path and output_path:
            if not os.path.exists(input_path):
                st.warning(f"知识库{input_path}不存在")
            if not os.path.exists(output_path):
                st.warning(f"{output_path}不存在")
            elif not os.path.isdir(output_path):
                st.warning(f"{output_path}不是目录")

            try:
                loader = Loader(input_path, chunk_size, chunk_overlap)
            except Exception as e:
                loader = None
                st.warning("文件加载和分割过程中出现错误:" + str(e))
            is_success = False
            if loader:
                chunks= loader.load_and_split_file(output_path)

                for idx,chunk in enumerate(chunks):
                    tmp = [chunk]
                    embeddings = llm_service_worker.get_embeddings({'texts': tmp, "bgem3_path": project_config.default_bgem3_path})
                    index_service_worker.index_texts({"keys": None, "texts": tmp, "embeddings": embeddings,
                                                               'collection_name': st.session_state.kb_name})
                st.success(f"文件已加载并分割完成！分割后文件路径:{loader.output_files}")
                is_success = True

            # 记录文件入库状态
            if is_success:
                for path in loader.output_files:
                    if not files_status_manager.check_file_exists(path, st.session_state.kb_name):
                        files_status_manager.add_file(path, st.session_state.kb_name)

        elif load_button:
            st.warning("参数不能为空。")
    elif input_method == '本地上传':
        st.markdown(
            '<span style="font-size: 12px; color: blue;">❗本地上传是指将电脑上的txt,pdf等格式的知识文件上传到服务器后，然后进行入库</span>',
            unsafe_allow_html=True)
        payload_file = st.file_uploader("请上传文件", type=["txt", "pdf"], key="payload_input")
        if 'now_upload_file' not in st.session_state:
            st.session_state.now_upload_file = ''
        if payload_file and not st.session_state.now_upload_file:
            file_name = payload_file.name
            file_name_prefix, file_ext = file_name.rsplit('.', 1)
            output_name_prefix = '%s_%s.%s' % (file_name_prefix, get_random_string(4), file_ext)
            output_path = os.path.join(default_upload_knowledge_base_dir, output_name_prefix) # 文件在服务器的位置
            with open(output_path, 'wb') as f:
                f.write(payload_file.read())
                st.success("文件已上传并保存到: %s" % output_path)
                st.session_state.now_upload_file = output_path
        if payload_file and st.session_state.now_upload_file:
            chunk_size = st.number_input("请输入块大小（字符数）:", min_value=1, value=512, key="chunk_size_key")
            chunk_overlap = st.number_input("请输入块重叠（字符数）:", min_value=1, value=8, key="chunk_overlap_key")
            load_button = st.button("加载并分割文件")
            input_path = st.session_state.now_upload_file
            if load_button:
                try:
                    loader = Loader(input_path, chunk_size, chunk_overlap)
                except Exception as e:
                    loader = None
                    st.warning("文件加载和分割过程中出现错误:" + str(e))
                is_success = False
                if loader:
                    chunks = loader.load_and_split_file(default_upload_knowledge_base_dir)

                    for idx,chunk in enumerate(chunks):
                        tmp = [chunk]
                        embeddings = llm_service_worker.get_embeddings(
                            {'texts': tmp, "bgem3_path": project_config.default_bgem3_path})
                        index_service_worker.index_texts({"keys": None, "texts": tmp, "embeddings": embeddings,
                                                          'collection_name': st.session_state.kb_name})
                    st.success(f"文件已加载并分割完成！分割后文件路径:{loader.output_files}")
                    is_success = True
                # 记录文件入库状态
                if is_success:
                    for path in loader.output_files:
                        if not files_status_manager.check_file_exists(path, st.session_state.kb_name):
                            files_status_manager.add_file(path, st.session_state.kb_name)



def rag_chain():
    # 用户输入query
    st.subheader('召回最匹配知识')
    query_input_key = "query_input_key"
    query_input = st.text_input("请输入查询", key=query_input_key)
    recall_button = st.button("召回")

    if recall_button and query_input:
        embeddings = llm_service_worker.get_embeddings(
            {'texts': [query_input], "bgem3_path": project_config.default_bgem3_path})
        search_results = index_service_worker.search_nearby({'collection_name':st.session_state.kb_name, "embeddings": embeddings})
        documents = search_results["documents"][0]
        st.write(documents)
        cross_scores = llm_service_worker.get_cross_scores({"texts_0": [query_input for i in range(len(documents))],
                                                            "texts_1": documents,
                                                            "rerank_path": project_config.default_rerank_path})
        st.header("Cross_score")
        st.write(cross_scores)
        cross_scores_values = cross_scores
        if cross_scores_values:
            max_score_index = cross_scores.index(max(cross_scores))
            best_match = documents[max_score_index]
            st.header("最佳匹配")
            st.write(f"Best Match: {best_match}")
            st.session_state.best_match = best_match
        else:
            st.warning("没有找到匹配的只是")

    st.subheader('RWKV-RAG-CHAT')

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    instruction_input = st.chat_input("请问您有什么问题？:", key="instruction_input")
    if 'best_match' in st.session_state and instruction_input:
        with st.chat_message("user"):
            st.markdown(instruction_input)
        st.session_state.chat_messages.append({"role": "User", "content": instruction_input})
        cmd = {
            "instruction": instruction_input,
            "input_text": st.session_state.best_match,
            #"token_count": 50,
            #"top_p": 0,
            "state_file": '',
            #"temperature": 1.0,
            "template_prompt": None,
            "base_model_path": None

        }
        sampling_results = llm_service_worker.sampling_generate(cmd)

        st.session_state.chat_messages.append({"role": "RWKV", "content": sampling_results})
        with st.chat_message("RWKV"):
            st.write(sampling_results)
        st.session_state.best_match = f"{st.session_state.best_match}"



def base_model_manager(current_base_model_name, default_base_model_path):
    st.title("模型管理")
    st.subheader("重启基底模型")
    st.markdown(
        '<span style="font-size: 16px; color: blue;">❗如果更换了基底模型可能影响到正在执行的任务。 更换后下次重启服务时基底模型就是本次更该后的模型</span>',
        unsafe_allow_html=True)
    st.write('当前基底模型: %s (%s)' % (current_base_model_name, default_base_model_path))

    base_model_list  = files_status_manager.get_base_model_list()
    active_base_models = OrderedDict()
    if base_model_list:
        names = []
        paths = []
        statuss = []
        create_times = []
        for line in base_model_list:
            names.append(line[0])
            paths.append(line[1])
            if line[2] == 1:
                active_base_models.setdefault(line[0], line[1])
                statuss.append('上线')
            else:
                statuss.append('下线')
            create_times.append(line[3])
    else:
        names = ['default']

    reload_base_model_name = st.selectbox("请选择要重启的基底模型:", [''] + list(active_base_models.keys()))
    if st.button("重启") and reload_base_model_name:
        new_base_model_path = active_base_models[reload_base_model_name]
        llm_service_worker.reload_base_model({'base_model_path': new_base_model_path})
        st.success('重启成功')
        project_config.set_llm_service_config(base_model_path=new_base_model_path)
        files_status_manager.create_or_update_using_base_model(reload_base_model_name)



    if reload_base_model_name == current_base_model_name:
        st.warning("需要重启的基底模型与当前基底模型一样。")


    st.subheader("基底模型列表")
    if base_model_list:
        df = pd.DataFrame({'名称': names, '路径': paths, '状态': statuss, '创建时间': create_times})
        st.dataframe(df, use_container_width=True)
    else:
        names = ['default']
        st.warning("没有找到基底模型。请先添加基底模型")

    st.subheader("新增基底模型")
    new_base_model_name = st.text_input("请输入基底模型的名称(唯一):", key='new_base_model_name')
    new_base_model_path = st.text_input("请输入基底模型的路径:", key='new_base_model_path')

    if st.button('添加'):
        if new_base_model_name:
           if not 3 <= len(new_base_model_name) <= 64:
               st.warning("基底模型的名称长度必须在3到64个字符之间。")
        else:
            st.warning("请输入基底模型名称。")
        if new_base_model_path:
            if not os.path.exists(new_base_model_path):
                st.warning("基底模型的路径不存在。")
        else:
            st.warning("请输入基底模型路径。")

        code= files_status_manager.add_base_model(new_base_model_name, new_base_model_path)
        if code == 0:
            st.warning(f"基底模型{new_base_model_name}已存在")
        else:
            st.success("基底模型添加成功。")
    st.subheader('修改基底模型')
    change_base_model_name = st.selectbox("请选择基底模型:", [''] + names, key='change_base_model_name')
    change_base_model_path = st.text_input("请输入基底模型的路径:", key='change_base_model_path')
    if st.button('修改') and change_base_model_name and change_base_model_path:
        files_status_manager.change_base_model(change_base_model_name, change_base_model_path)
        st.success("基底模型修改成功。")

    st.subheader("激活基底模型")
    st.markdown(
        '<span style="font-size: 16px; color: blue;">状态是上线的基底模型才能使用</span>',
        unsafe_allow_html=True)
    active_base_model_name = st.selectbox("请选择基底模型:", [''] + names, key='active_base_model_name')
    if st.button('激活') and active_base_model_name:
        files_status_manager.active_base_model(active_base_model_name)
        st.success("基底模型激活成功。")

    st.subheader("下线基底模型")
    offline_base_model_name = st.selectbox("请选择基底模型:", [''] + names, key='offline_base_model_name')
    if offline_base_model_name == 'default':
        st.warning("default 模型不能下线，可以通过修改default模型的路径来实现你的需求。")
    if st.button('下线') and offline_base_model_name:
        files_status_manager.offline_base_model(offline_base_model_name)
        st.success("基底模型下线成功。")




def main():
    # 初始化客户端

    tabs_title = ["模型管理", "知识库管理", "知识入库", "知识问答"]


    default_base_model_path = project_config.default_base_model_path
    # default_state_path = project_config.default_state_path

    set_page_style()

    with st.sidebar:
        st.header("RWKV RAGQ")
        st.write('\n')
        # 创建垂直排列的标签页
        app_scenario = st.radio('', tabs_title)

        st.write('\n')
        st.markdown("""
        <hr style="border: 1px solid #CCCCCC; margin-top: 20px; margin-bottom: 20px;">
        """, unsafe_allow_html=True)
        st.write('\n')

        # 当前知识库
        collections = index_service_worker.show_collections({})
        if collections:
            collection_name_list = [i[0] for i in collections]
        else:
            collection_name_list = []
        default_base_model_name = files_status_manager.get_base_model_name_by_path(default_base_model_path) or 'default'
        st.session_state.kb_name = st.selectbox("正在使用的知识库", collection_name_list, )
        st.session_state.base_model_path = st.selectbox('基底RWKV模型', [default_base_model_name])
        # st.session_state.state_file_path = st.selectbox("记忆状态", [default_state_path])

    if app_scenario == tabs_title[0]:
        base_model_manager(default_base_model_name, default_base_model_path)
    elif app_scenario == tabs_title[1]:
        knowledgebase_manager()
    elif app_scenario == tabs_title[2]:
        internet_search()

    else:
        st.title("知识问答")
        rag_chain()



if __name__ == "__main__":

    main()
