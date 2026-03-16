def orderDocument(metadatas, documents):
    map = []
    for index, metadata in enumerate(metadatas):
        chunk_number = metadata['page']
        page_number = metadata['index']
        map.append((index, int(page_number), int(chunk_number)))
    sorted_data = sorted(map, key=lambda x: (x[1], x[2]))
    sorted_documents = [documents[k[0]] for k in sorted_data]
    return sorted_documents

def orderChats(metdatas,documents):
    dummy = [i for i in range(len(metdatas))]
    dummy = sorted(dummy, key=lambda x: metdatas[x]["timestamp"])
    sorted_chats = [documents[i] for i in dummy]
    return sorted_chats
