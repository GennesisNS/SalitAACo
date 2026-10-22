class IconPicture:
    """
    For a model whose picture is an emoji (`emoji`) or a picture someone
    uploaded in its place (`icon_image`, with its content type in `icon_mime`):
    a guardian's board, an admin's word, a guardian's tile. Like every upload,
    the picture is served only by a login-protected view.
    """

    @property
    def has_icon_image(self):
        return bool(self.icon_image)

    def set_icon_image(self, file_name, content, mime):
        """Use an uploaded picture in place of the emoji, removing the picture before."""
        self.remove_icon_image(save=False)
        self.icon_image.save(file_name, content, save=False)
        self.icon_mime = mime
        self.emoji = ""
        self.save()

    def remove_icon_image(self, save=True):
        if self.icon_image:
            self.icon_image.delete(save=False)
        self.icon_mime = ""
        if save:
            self.save()
