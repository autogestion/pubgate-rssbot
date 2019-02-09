import re

find_tag_scheme = re.compile(r"(?!<a[^>]*?>)(?P<tagged>#\w+)(?![^<]*?</a>)")
find_image_scheme = re.compile(r'(?P<image_construction><img\b[^>]*src="(?P<image_url>[^"]+?)"[^>]*?\/>)')
# find_link_around_image_scheme = re.compile(r"<a\b[^>]*>(.*?)<img\b(.*?)<\/a>")


def process_tags(entry, content, bot):
    extra_tag_list = []
    footer_tags = ""

    # collect tags marked as "labels" in the post
    if "tags" in entry:
        extra_tag_list = [tag["term"] for tag in entry["tags"]]

    # collect hardcoded tags from config
    if bot["details"]["rssbot"]["tags"]:
        extra_tag_list.extend(bot["details"]["rssbot"]["tags"])

    # Make extra text list clickable
    extra_tag_list = list(set(["#" + tag for tag in extra_tag_list]))
    extra_tag_list_clickable = [f"<a href='' rel='tag'>{tag}</a>" for tag in extra_tag_list]

    # collect tags from the post body
    intext_tag_list = re.findall(find_tag_scheme, content)
    if intext_tag_list:
        content = re.sub(find_tag_scheme, r"<a href='' rel='tag'>\g<tagged></a>", content)

    # Set tags as mastodon service info
    apub_tag_list = set(intext_tag_list + extra_tag_list)
    object_tags = [{
                       "href": "",
                       "name": tag,
                       "type": "Hashtag"
                   } for tag in apub_tag_list]

    if extra_tag_list_clickable:
        footer_tags = f"<br><br> {' '.join(extra_tag_list_clickable)}"

    return content, footer_tags, object_tags


def move_image_to_attachment(content, attachment_object):
    # collect images from the post body
    intext_image_list = re.findall(find_image_scheme, content)

    if intext_image_list:
        # delete images form text
        content = re.sub(find_image_scheme, r"", content)

        # insert link to image into attachments
        attachment_object += [{
            "type": "Document",
            "mediaType": "image/jpeg",
            "url": image[1],
            "name": "null"
            } for image in intext_image_list]

    return content
