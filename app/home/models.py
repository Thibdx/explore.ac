from django.db import models

from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase

from wagtail.core.models import Page, Orderable
from wagtail.core.fields import RichTextField
from django.contrib.postgres.fields import ArrayField
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel, InlinePanel, StreamFieldPanel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index

from wagtail.core import blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.snippets.blocks import SnippetChooserBlock
from wagtail.snippets.models import register_snippet
from wagtail.embeds.blocks import EmbedBlock

from home.custom_blocks import WdQueryBlock

class HomePage(Page):

    '''
    These are homepages explore.ac and for sub-sites such as chronic-pain.reviews
    These also store the data relative to the focus.
    '''

    # Database fields
    
    ## site url, used for the logo
    url = models.URLField(blank=True)
    
    ## Intro message printed over the image
    intro = RichTextField(blank=True)

    ## Full width intro image
    intro_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    ## Intro message printed at the start of articles
    intro_articles = RichTextField(blank=True)

    # Search index configuration

    search_fields = Page.search_fields + [
        index.FilterField('url'),
        index.FilterField('intro'),
        index.FilterField('intro_articles'),
    ]

    # Editor panels configuration

    content_panels = Page.content_panels + [
        FieldPanel('url'),
        FieldPanel('wd_Qids'),
        FieldPanel('keywords'),
        FieldPanel('intro', classname="full"),
        FieldPanel('intro_articles', classname="full"),
    ]

    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
        ImageChooserPanel('intro_image'),
    ]

    # Update context to include only published posts, ordered by reverse-chron

    def get_context(self, request):
        context = super().get_context(request)
        articlepages = self.get_children().live().order_by('-first_published_at')
        context['articlepages'] = articlepages
        return context


class ArticlePage(Page):

    '''
    Articles pages handle both hand written articles and Wikidata query results.
    It uses StremField for the best flexibility.
    A StreamField block is generated for Wikidata queries results.
    '''

    # Database fields

    body = StreamField([
        ('heading', blocks.CharBlock(classname="full title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
        ('quote', BlockQuoteBlock()),
        ('page', PageChooserBlock()),
        ('document', DocumentChooserBlock()),
        ('embed', EmbedBlock()),
        ('wikidata_query', WdQueryBlock()),
    ])
    
    date = models.DateField("Post date")
    last_edit_date = models.DateField(auto_now=True)

    feed_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)


    # Search index configuration

    search_fields = Page.search_fields + [
        index.SearchField('body'),
        index.FilterField('date'),
        index.FilterField('last_edit_date'),
    ]


    # Editor panels configuration

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('subtitle'),
            FieldPanel('date'),
            FieldPanel('tags'),
        ], heading="Article information"),
        FieldPanel('body', classname="full"),
    ]

    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
        ImageChooserPanel('feed_image'),
    ]

class ArticleTagPage(TaggedItemBase):
    '''
    Add tagging capacity to pages.
    Based on Django tag system.
    '''
    content_object = ParentalKey(
        'ArticlePage',
        related_name='tagged_items',
        on_delete=models.CASCADE
    )

class ArticleTagIndexPage(Page):
    '''
    Adding a page type to display a list of tags
    '''

    def get_context(self, request):

        # Filter by tag
        tag = request.GET.get('tag')
        articlepages = ArticlePage.objects.filter(tags__name=tag)

        # Update template context
        context = super().get_context(request)
        context['articlepages'] = articlepages
        return context

class WikidataClass(Page):

    '''
    This type of page display a table with :
       - Items as rows
       - Featured Pids as columns
    It is also used to store the featured Pids per class for ItemPages.
    '''

    # Database fields

    class_Qid = models.CharField(max_length=255)
    featured_Pids = ArrayField(
            models.CharField(max_length=255, blank=True)
        )

    # Search index configuration

    search_fields = Page.search_fields + [
        index.SearchField('class_Qid'),
        index.SearchField('featured_Pids'),
    ]

    # Editor panels configuration

    content_panels = Page.content_panels + [
        FieldPanel('class_Qid'),
        FieldPanel('featured_Pids'),
    ]

    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
    ]


## Categories

@register_snippet
class BlogCategory(models.Model):
    name = models.CharField(max_length=255)
    icon = models.ForeignKey(
        'wagtailimages.Image', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )

    panels = [
        FieldPanel('name'),
        ImageChooserPanel('icon'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'blog categories'


class ArticleCategory(Page):

    '''
    Articles' categories.
    Used for a limited set of sitewide categories.
    '''

    # Database fields

    ## Basic
    name = models.CharField(max_length=255)
    icon = models.ForeignKey(
        'wagtailimages.Image', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )   

    ## Intro message printed over the image
    intro = RichTextField(blank=True)

    ## Full width intro image
    intro_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    # Search index configuration

    search_fields = Page.search_fields + [
        FieldPanel('name'),
        ImageChooserPanel('icon'),
        index.FilterField('intro'),
    ]

    # Editor panels configuration

    content_panels = Page.content_panels + [
        FieldPanel('url'),
        FieldPanel('wd_Qids'),
        FieldPanel('keywords'),
        FieldPanel('intro', classname="full"),
    ]

    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
        ImageChooserPanel('intro_image'),
    ]

    # Update context to include only published posts, ordered by reverse-chron

  #  def get_context(self, request):
  #      context = super().get_context(request)
  #      articlepages = self.get_children().live().order_by('-first_published_at')
  #      context['articlepages'] = articlepages
  #      return context
