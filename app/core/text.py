import re

from tts.app import settings


def get_sentences(text: str) -> [str]:
    lines = re.split("([?!.,;:])", text)
    lines = s_split_large_lines(lines)
    lines = s_merge_to_max(lines, [])

    return lines


def s_merge_to_max(s_in: [], s_out: []):
    n = ""
    while s_in:
        e = s_in.pop(0)
        if (
            len((n + e).split()) <= settings.APP_SENTENCE_MAX_WORDS
            or len(e.split()) > settings.APP_SENTENCE_MAX_WORDS
        ):
            n += e
        else:
            s_in.insert(0, e)
            break

    s_out.append(n.strip())
    if s_in:
        s_merge_to_max(s_in, s_out)

    return s_out


def s_split_large_lines(lines: []):
    for e in lines:
        words = e.split()

        if len(words) > settings.APP_SENTENCE_MAX_WORDS:
            i = lines.index(e)
            lines.remove(e)

            while words:
                end = (
                    settings.APP_SENTENCE_MAX_WORDS
                    if len(words) > settings.APP_SENTENCE_MAX_WORDS
                    else len(words)
                )
                lines.insert(i, " ".join(words[0:end]))
                words = words[end:]
                i += 1

    return lines
