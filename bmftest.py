with open("test.bmf", "rb") as bmf:
    bmf.seek(1, 0)
    start = bmf.read(3)
    start = (start[0] << 16) + (start[1] << 8) + start[2]
    bmf.seek(9, 0)
    words = bmf.read(start - 9).decode("utf-8")

bmf_file = open("test.bmf", "rb")


def get_bitmap(word):
    index = words.find(word)
    if index == -1:
        return [0x00, 0x7F, 0x7F, 0x67, 0x6B, 0x75, 0x7A, 0x7D, 0x7D, 0x7A, 0x75, 0x6B, 0x67, 0x7F, 0x7F, 0x00, 0x00,
                0xFE, 0xFE, 0xE6, 0xD6, 0xAE, 0x5E, 0xBE, 0xBE, 0x5E, 0xAE, 0xD6, 0xE6, 0xFE, 0xFE, 0x00]
    bmf_file.seek(start + 32 * index, 0)
    return list(bmf_file.read(32))


print(words)
a = get_bitmap("!")
print(a)