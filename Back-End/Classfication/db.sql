-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.cleaned_news (
  article_id uuid NOT NULL,
  article_title text,
  article_url text,
  content text,
  media text,
  story_id uuid,
  CONSTRAINT cleaned_news_pkey PRIMARY KEY (article_id),
  CONSTRAINT cleaned_news_story_id_fkey FOREIGN KEY (story_id) REFERENCES public.stories(story_id)
);
CREATE TABLE public.generated_image (
  story_id uuid NOT NULL,
  image text,
  description text,
  CONSTRAINT generated_image_pkey PRIMARY KEY (story_id),
  CONSTRAINT generated_image_story_id_fkey FOREIGN KEY (story_id) REFERENCES public.single_news(story_id)
);
CREATE TABLE public.keywords (
  keyword text NOT NULL,
  CONSTRAINT keywords_pkey PRIMARY KEY (keyword)
);
CREATE TABLE public.keywords_map (
  story_id uuid NOT NULL DEFAULT gen_random_uuid(),
  keyword text NOT NULL,
  CONSTRAINT keywords_map_pkey PRIMARY KEY (story_id, keyword),
  CONSTRAINT keywords_map_story_id_fkey FOREIGN KEY (story_id) REFERENCES public.single_news(story_id),
  CONSTRAINT keywords_map_keyword_fkey FOREIGN KEY (keyword) REFERENCES public.keywords(keyword)
);
CREATE TABLE public.relative_news (
  id uuid NOT NULL,
  reason text,
  src_story_id uuid,
  dst_story_id uuid,
  CONSTRAINT relative_news_pkey PRIMARY KEY (id),
  CONSTRAINT relative_news_dst_story_id_fkey FOREIGN KEY (dst_story_id) REFERENCES public.single_news(story_id),
  CONSTRAINT relative_news_src_story_id_fkey FOREIGN KEY (src_story_id) REFERENCES public.single_news(story_id)
);
CREATE TABLE public.single_news (
  story_id uuid NOT NULL,
  category text,
  total_articles integer,
  news_title text,
  ultra_short text,
  short text,
  long text,
  generated_date text,
  CONSTRAINT single_news_pkey PRIMARY KEY (story_id),
  CONSTRAINT single_news_story_id_fkey FOREIGN KEY (story_id) REFERENCES public.stories(story_id)
);
CREATE TABLE public.stories (
  story_id uuid NOT NULL,
  story_url text,
  story_title text,
  category text,
  crawl_date text,
  CONSTRAINT stories_pkey PRIMARY KEY (story_id)
);
CREATE TABLE public.term (
  term text NOT NULL,
  definition text,
  example text,
  CONSTRAINT term_pkey PRIMARY KEY (term)
);
CREATE TABLE public.term_map (
  story_id uuid NOT NULL DEFAULT gen_random_uuid(),
  term text NOT NULL DEFAULT now(),
  CONSTRAINT term_map_pkey PRIMARY KEY (story_id, term),
  CONSTRAINT term_map_term_fkey FOREIGN KEY (term) REFERENCES public.term(term),
  CONSTRAINT term_map_story_id_fkey FOREIGN KEY (story_id) REFERENCES public.single_news(story_id)
);
CREATE TABLE public.topic (
  topic_id uuid NOT NULL DEFAULT gen_random_uuid(),
  topic_title text NOT NULL,
  topic_short text,
  topic_long text,
  ref_num integer,
  view_num integer,
  generated_date text,
  update_date text,
  mind_map_detail json,
  CONSTRAINT topic_pkey PRIMARY KEY (topic_id)
);
CREATE TABLE public.topic_branch (
  topic_branch_id uuid NOT NULL DEFAULT gen_random_uuid(),
  topic_id uuid NOT NULL DEFAULT gen_random_uuid(),
  topic_branch_title text,
  topic_branch_content text,
  CONSTRAINT topic_branch_pkey PRIMARY KEY (topic_branch_id),
  CONSTRAINT topic_branch_topic_id_fkey FOREIGN KEY (topic_id) REFERENCES public.topic(topic_id)
);
CREATE TABLE public.topic_branch_news_map (
  topic_branch_id uuid NOT NULL,
  story_id uuid NOT NULL,
  CONSTRAINT topic_branch_news_map_pkey PRIMARY KEY (topic_branch_id, story_id),
  CONSTRAINT topic_news_map_story_id_fkey FOREIGN KEY (story_id) REFERENCES public.single_news(story_id),
  CONSTRAINT topic_news_map_topic_branch_id_fkey FOREIGN KEY (topic_branch_id) REFERENCES public.topic_branch(topic_branch_id)
);
CREATE TABLE public.topic_news_map (
  topic_id uuid NOT NULL DEFAULT gen_random_uuid(),
  story_id uuid NOT NULL,
  CONSTRAINT topic_news_map_pkey PRIMARY KEY (topic_id, story_id),
  CONSTRAINT topic_news_map_topic_id_fkey FOREIGN KEY (topic_id) REFERENCES public.topic(topic_id),
  CONSTRAINT topic_news_map_story_id_fkey1 FOREIGN KEY (story_id) REFERENCES public.single_news(story_id)
);