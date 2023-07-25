from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.http import Http404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from blog.forms import CommentForm, PostForm, UserForm
from blog.models import Category, Comment, Post, User
from blog.mixin import (PaginatorMixin, CommentMixin,
                        DispatchMixin)


class IndexListView(PaginatorMixin, ListView):
    template_name = 'blog/index.html'
    context_object_name = 'page_obj'

    def get_queryset(self):
        return Post.objects.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lt=timezone.now(),
        ).order_by('-pub_date').annotate(comment_count=Count("comments"))


class PostDetailView(PaginatorMixin, DetailView):
    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'

    def get_object(self, queryset=None):
        post = get_object_or_404(Post, pk=self.kwargs["pk"])
        if (not post.is_published or not post.category.is_published
                or post.pub_date > timezone.now()):
            if self.request.user != post.author:
                raise Http404("Post does not exist")
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = Comment.objects.filter(post=self.object)
        return context


class CategoryListView(PaginatorMixin, ListView):
    template_name = 'blog/category.html'

    def dispatch(self, request, *args, **kwargs):
        get_object_or_404(
            Category,
            slug=kwargs["category_slug"],
            is_published=True
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return Post.objects.filter(
            category__slug=self.category.slug,
            pub_date__lt=timezone.now(),
            is_published=True,
        ).annotate(comment_count=Count('comments')).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class ProfileListView(PaginatorMixin, ListView):
    model = Post
    template_name = 'blog/profile.html'

    def get_queryset(self):
        author = get_object_or_404(User, username=self.kwargs.get('username'))
        return author.posts.filter(
            author__username__exact=self.kwargs.get('username')
        ).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(User, username=self.kwargs.get(
            'username'
        )
        )
        return context


class AddCommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    template_name = 'blog/comment.html'
    form_class = CommentForm

    def form_valid(self, form):
        self.post_comment = get_object_or_404(
            Post, pk=self.kwargs['post_id']
        )
        form.instance.author = self.request.user
        form.instance.post = self.post_comment
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'pk': self.post_comment.pk}
        )


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user}
        )

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, DispatchMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    posts = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'pk': self.posts.pk})


class PostDeleteView(LoginRequiredMixin, DispatchMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')
    pk_url_kwarg = 'post_id'


class CommentUpdateView(CommentMixin, LoginRequiredMixin, UpdateView):
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'


class CommentDeleteView(CommentMixin, LoginRequiredMixin, DeleteView):
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'blog/user.html'
    success_url = reverse_lazy('blog:index')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username})
