import re


find_image_scheme = re.compile(r'(?P<image_construction><img\b[^>]*src="(?P<image_url>[^"]+?)"[^>]*?\/>)')
# find_link_around_image_scheme = re.compile(r"<a\b[^>]*>(.*?)<img\b(.*?)<\/a>")




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
