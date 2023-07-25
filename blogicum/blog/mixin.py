from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseForbidden
from django.urls import reverse

from blog.forms import CommentForm
from blog.models import Comment, Post

OBJ_COUNT = 10


class PaginatorMixin:
    paginate_by = OBJ_COUNT


class CommentMixin:
    model = Comment
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        comment_update = get_object_or_404(Comment, pk=kwargs["comment_id"])
        if comment_update.author != request.user:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'pk': self.kwargs['post_id']}
        )


class DispatchMixin:
    model = Post
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        self.posts = get_object_or_404(Post, pk=kwargs.get('post_id'))
        if self.posts.author != request.user:
            return redirect('blog:post_detail', self.kwargs.get('post_id'))
        return super().dispatch(request, *args, **kwargs)
