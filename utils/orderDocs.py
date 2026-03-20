def orderDocument( documents):
    map = []
    for document in documents:
        chunk_number = documents['chunk_index']
        page_number = documents['chunkindex']
        if type(page_number)  == str:
            page_number = int(float(page_number))
        if type(chunk_number)  == str:
            chunk_number = int(float(chunk_number))

        map.append((index, page_number, chunk_number))
    sorted_data = sorted(map, key=lambda x: (x[1], x[2]))
    sorted_documents = [documents[k[0]] for k in sorted_data]
    return sorted_documents

def orderChats(metdatas,documents):
    dummy = [i for i in range(len(metdatas))]
    dummy = sorted(dummy, key=lambda x: metdatas[x]["timestamp"])
    sorted_chats = [documents[i] for i in dummy]
    return sorted_chats


def sort_docs(points):
    def parse_chunk(chunk):
        if isinstance(chunk, (int, float)):
            return (int(chunk), 0)
        if isinstance(chunk, str):
            return tuple(int(p) for p in chunk.split("."))
        return (0, 0)

    sorted_points = sorted(
        points,
        key=lambda p: (
            p.payload.get("page", 0),
            parse_chunk(p.payload.get("chunk_index", 0)),
        ),
    )
    return [p.payload.get("text", "") for p in sorted_points]


def sort_chats(points):
    sorted_points = sorted(points, key=lambda p: p.payload.get("timestamp", ""))
    return [p.payload.get("text", "") for p in sorted_points]
