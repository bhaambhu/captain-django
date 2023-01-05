from django.db.models import fields
from django.db.models.fields.related import RelatedField
from rest_framework import serializers
from rest_framework.fields import BooleanField, CharField
from rest_framework.relations import PrimaryKeyRelatedField
from knowledge.models import Subject, Topic, Path, PathTopicSequence, TopicProgress

class ChildrenSerializer(serializers.ModelSerializer):
    # d_count = serializers.IntegerField(source='get_descendant_count')
    class Meta:
        model = Subject
        fields = ('id', 'name', 'display_name', 'children')

class TopicListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ('id', 'title', 'about', 'author', 'subject', 'requires', 'breadcrumbs')

class BreadcrumbSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ('id', 'name')

class SubjectSerializer(serializers.ModelSerializer):
    hasChildren = BooleanField(source='get_descendant_count', read_only=True)
    isChildrenLoading = BooleanField(default=False, read_only=True)
    isExpanded = BooleanField(default=False, read_only=True)
    # breadcrumbs = BreadcrumbSerializer(many=True, source='get_ancestors(include_self=True)')
    class Meta:
        model = Subject
        fields = ('id', 'children', 'hasChildren', 'isExpanded', 'isChildrenLoading', 'name', 'display_name', 'breadcrumbs', 'parent')
        extra_kwargs = {'children': {'required':False}}
        # depth = 1

class SubjectDetailSerializer(serializers.ModelSerializer):
    topics = TopicListSerializer(many=True, read_only=True)
    class Meta:
        model = Subject
        fields = ('id', 'name', 'about', 'topics', 'breadcrumbs')
        depth = 1
    # def update(self, instance, validated_data):
        
    #     # first save the Path meta info
    #     instance.title = validated_data.get('title', instance.title)
    #     instance.about = validated_data.get('about', instance.about)        
    #     # First delete existing topic_sequence data for this path
    #     instance.topic_sequence.all().delete()
    #     instance.save()
        
    #     topic_seq_data = self.initial_data['topic_sequence']
    #     for item in topic_seq_data:
    #         order = item['order']
    #         topic_id = item['topic']['id']
    #         try:
    #             PathTopicSequence.objects.create(order=order, path=instance, topic_id=topic_id)
    #         except:
    #             raise serializers.ValidationError("Error in given Topic Sequence: "+str(order))

    #     return instance

class TopicProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicProgress
        fields = ('verifiable', 'completed')

class TopicListProgressSerializer(serializers.ModelSerializer):
    progress = TopicProgressSerializer(many=True, source='filtered_progress')
    class Meta:
        model = Topic
        fields = ('id', 'title', 'about', 'requires', 'breadcrumbs', 'progress')

class TopicProgressMinSerializer(serializers.ModelSerializer):
    progress = TopicProgressSerializer(many=True)
    class Meta:
        model = Topic
        fields = ('id', 'title', 'requires', 'progress')

class TopicDetailSerializer(serializers.ModelSerializer):
    requires = TopicProgressMinSerializer(many=True, read_only=True)
    class Meta:
        model = Topic
        fields = ('id', 'title', 'about', 'author', 'requires', 'subject', 'breadcrumbs', 'assessor', 'steps' )

class PathTopicSequenceProgressSerializer(serializers.ModelSerializer):
    topic = TopicListProgressSerializer()
    class Meta:
        model = PathTopicSequence
        fields = ('order', 'topic')
    
class PathDetailRetrieveSerializer(serializers.ModelSerializer):
    topic_sequence = PathTopicSequenceProgressSerializer(many=True)
    class Meta:
        model = Path
        fields = ('id', 'published', 'title', 'about', 'author', 'topic_sequence')

class PathTopicSequenceSerializer(serializers.ModelSerializer):
    topic = TopicListSerializer()
    class Meta:
        model = PathTopicSequence
        fields = ('order', 'topic')

class PathDetailSerializer(serializers.ModelSerializer):
    topic_sequence = PathTopicSequenceSerializer(many=True)
    class Meta:
        model = Path
        fields = ('id', 'published', 'title', 'about', 'author', 'topic_sequence')
    def update(self, instance, validated_data):
        
        # first save the Path meta info
        instance.title = validated_data.get('title', instance.title)
        instance.about = validated_data.get('about', instance.about)
        instance.published = validated_data.get('published', instance.published)
        instance.author = validated_data.get('author', instance.author)

        # First delete existing topic_sequence data for this path
        instance.topic_sequence.all().delete()
        instance.save()
        
        topic_seq_data = self.initial_data['topic_sequence']
        for item in topic_seq_data:
            order = item['order']
            topic_id = item['topic']['id']
            try:
                PathTopicSequence.objects.create(order=order, path=instance, topic_id=topic_id)
            except:
                raise serializers.ValidationError("Error in given Topic Sequence: "+str(order))

        return instance

class PathListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Path
        fields = ('id', 'title', 'about', 'published', 'author')

# class TopicSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Topic
#         fields = ('id', 'title', 'about', 'author', 'status')
#         #slug, parent, title, about, explanation, author, status

# class TopicDetailSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Topic
#         fields = ('id', 'title', 'about',
#                   'author', 'status', 'explanation')
