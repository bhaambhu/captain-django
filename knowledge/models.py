from os import stat
from django.db import models
from django.conf import settings
from mptt.models import MPTTModel, TreeForeignKey
from slugger import AutoSlugField
import calendar

# A subject is a collection of topics


class Subject(MPTTModel):
    class Meta:
        unique_together = (('name', 'parent', ), )

    class MPTTMeta:
        order_insertion_by = ['name']
    name = models.CharField(max_length=200)
    parent = TreeForeignKey('self', on_delete=models.SET_NULL,
                            related_name='children', null=True, blank=True)
    display_name = models.CharField(max_length=250, blank=True, null=True)
    about = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return self.name

    def breadcrumbs(self):
        ex = []
        for sub in self.get_ancestors(include_self=True):
            ex.append({"id": sub.id, "name": sub.name})
        return ex

    def delete(self, *args, **kwargs):
        # Move all its children to parent
        for child in self.get_children():
            child.move_to(self.parent, position="last-child")
            child.save()
        # Move all its topics to parent subject
        for topic in self.topics.all():
            if self.parent.id == 1:
                topic.subject = None
            else:
                topic.subject = self.parent
            topic.save()
        return super().delete(*args, **kwargs)


class Topic(models.Model):
    slug = AutoSlugField(populate_from='title')
    title = models.CharField(max_length=250, blank=True, null=True)
    about = models.CharField(max_length=500, blank=True)
    subject = TreeForeignKey(
        Subject, on_delete=models.SET_NULL, related_name="topics", blank=True, null=True)
    requires = models.ManyToManyField(
        'self', symmetrical=False, related_name="required_for", blank=True)
    steps = models.JSONField(default=list, blank=True)
    assessor = models.JSONField(default=dict, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='topics', null=True)

    def __str__(self):
        return self.title

    def breadcrumbs(self):
        ex = []
        if self.subject != None:
            for sub in self.subject.get_ancestors(include_self=True):
                ex.append({"id": sub.id, "name": sub.name})
        return ex


class Path(models.Model):
    class PublishedPaths(models.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(published=True)
    # options = (
    #     ('published', 'Published'),
    #     ('draft', 'Draft'),
    # )
    slug = AutoSlugField(populate_from='title')
    title = models.CharField(max_length=250, blank=True, null=True)
    about = models.CharField(max_length=500, blank=True, null=True)
    topics = models.ManyToManyField(
        Topic, through='PathTopicSequence', related_name="paths")
    published = models.BooleanField(default=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='paths', null=True)
    # status = models.CharField(
    #     max_length=10, choices=options, default='draft')

    objects = models.Manager()  # default manager
    publishedPaths = PublishedPaths()  # custom manager

    def __str__(self):
        return self.title


class PathTopicSequence(models.Model):
    order = models.PositiveIntegerField()
    path = models.ForeignKey(
        Path, on_delete=models.CASCADE, related_name="topic_sequence")
    topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name="in_paths")

    class Meta:
        unique_together = ['path', 'order']
        ordering = ['order']

    def __str__(self):
        return self.path.title + " - " + str(self.order) + ": "+self.topic.title

# Stores the various top-level information about an exam


class ExamDescription(models.Model):
    name = models.CharField(max_length=200, blank=True)
    shortform = models.CharField(max_length=50, blank=True)
    job_title = models.CharField(max_length=200, blank=True)
    about = models.TextField(blank=True)

    def __str__(self):
        return self.name+" "+self.job_title

# To store individual exams (papers), it pulls exam description from model "ExamDescription"


class Exam(models.Model):
    subject = models.CharField(max_length=200, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    month = models.PositiveIntegerField(null=True, blank=True)
    sub_paper = models.CharField(max_length=50, blank=True, null=True)
    temp_title = models.CharField(max_length=200, blank=True)
    description = models.ForeignKey(
        ExamDescription, null=True, blank=True, on_delete=models.SET_NULL, related_name="papers")

    def __str__(self):
        return self.description.name+" "+self.description.shortform + " " + str(self.year) + " " + (calendar.month_abbr[self.month] if self.month else "") + ((" Paper-" + str(self.sub_paper) if self.sub_paper else ""))


class TopicProgress(models.Model):
    verifiable = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='topics_progress')
    topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name="progress")

    class Meta:
        unique_together = ['student', 'topic']

    def __str__(self):
        return self.student.display_name + " - " + self.topic.title

# This model has the actual hierarchy of topics that we use in our system
# class Topic(models.Model):
#     class Meta:
#         unique_together = (('slug', 'parent', ), )

#     class TopicObjects(models.Manager):
#         def get_queryset(self):
#             return super().get_queryset().filter(status='published')

#     options = (
#         ('published', 'Published'),
#         ('draft', 'Draft'),
#     )

#     slug = AutoSlugField(populate_from='title')
#     parent = models.ForeignKey(
#         'self', on_delete=models.SET_NULL, related_name='children', null=True, blank=True)
#     title = models.CharField(max_length=250, blank=True, null=True)
#     about = models.CharField(max_length=500, blank=True)
#     explanation = models.TextField(blank=True)
#     author = models.ForeignKey(
#         settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='topics', null=True)
#     status = models.CharField(
#         max_length=10, choices=options, default='published')

#     objects = models.Manager()  # default manager
#     topicobjects = TopicObjects()  # custom manager

#     def __str__(self):
#         return self.slug


class Concept(models.Model):
    name = models.CharField(max_length=200)
    display_name = models.CharField(max_length=250, blank=True, null=True)
    about = models.CharField(max_length=500, blank=True)
    explanation = models.TextField(blank=True)

    def __str__(self):
        return self.name


# Model that we used to store images in Django
class KnowledgeImage(models.Model):
    image = models.ImageField(upload_to='images/')


# A model to be used to "Group" certain questions together
# Currently not being used in this project
class QuestionGroup(models.Model):
    common_data = models.TextField(blank=True)
    explanation = models.TextField(blank=True)

    def __str__(self):
        return self.common_data[:20]+"..."


# The question model
class Question(models.Model):
    question_text = models.TextField()
    explanation = models.TextField(blank=True)
    difficulty = models.CharField(max_length=100, blank=True)
    question_group = models.ForeignKey(
        QuestionGroup, blank=True, null=True, on_delete=models.SET_NULL)
    exams = models.ManyToManyField(Exam, blank=True)
    concepts = models.ManyToManyField(
        Concept, blank=True, related_name="questions")
    topics = models.ManyToManyField(Topic, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='questions', null=True)

    def __str__(self):
        return self.question_text[:20]+"..."

# Works with the Question model


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    option = models.TextField()
    correct = models.BooleanField()

    def __str__(self):
        return self.option[:20]+"..."
