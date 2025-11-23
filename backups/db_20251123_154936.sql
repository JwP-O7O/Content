--
-- PostgreSQL database dump
--

-- Dumped from database version 17.0
-- Dumped by pg_dump version 17.0

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: contentformat; Type: TYPE; Schema: public; Owner: content_creator_user
--

CREATE TYPE public.contentformat AS ENUM (
    'SINGLE_TWEET',
    'THREAD',
    'BLOG_POST',
    'TELEGRAM_MESSAGE',
    'IMAGE_POST'
);


ALTER TYPE public.contentformat OWNER TO content_creator_user;

--
-- Name: insighttype; Type: TYPE; Schema: public; Owner: content_creator_user
--

CREATE TYPE public.insighttype AS ENUM (
    'BREAKOUT',
    'BREAKDOWN',
    'SENTIMENT_SHIFT',
    'VOLUME_SPIKE',
    'NEWS_IMPACT',
    'TECHNICAL_PATTERN',
    'CORRELATION'
);


ALTER TYPE public.insighttype OWNER TO content_creator_user;

--
-- Name: teststatus; Type: TYPE; Schema: public; Owner: content_creator_user
--

CREATE TYPE public.teststatus AS ENUM (
    'ACTIVE',
    'COMPLETED',
    'PAUSED',
    'CANCELLED'
);


ALTER TYPE public.teststatus OWNER TO content_creator_user;

--
-- Name: usertier; Type: TYPE; Schema: public; Owner: content_creator_user
--

CREATE TYPE public.usertier AS ENUM (
    'FREE',
    'BASIC',
    'PREMIUM',
    'VIP'
);


ALTER TYPE public.usertier OWNER TO content_creator_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ab_test_variants; Type: TABLE; Schema: public; Owner: content_creator_user
--

CREATE TABLE public.ab_test_variants (
    id integer NOT NULL,
    test_id integer NOT NULL,
    variant_name character varying(50) NOT NULL,
    is_control boolean,
    variant_config json NOT NULL,
    impressions integer,
    clicks integer,
    engagement_count integer,
    conversion_count integer,
    click_through_rate double precision,
    engagement_rate double precision,
    conversion_rate double precision,
    sample_size integer,
    created_at timestamp without time zone
);


ALTER TABLE public.ab_test_variants OWNER TO content_creator_user;

--
-- Name: ab_test_variants_id_seq; Type: SEQUENCE; Schema: public; Owner: content_creator_user
--

CREATE SEQUENCE public.ab_test_variants_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ab_test_variants_id_seq OWNER TO content_creator_user;

--
-- Name: ab_test_variants_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: content_creator_user
--

ALTER SEQUENCE public.ab_test_variants_id_seq OWNED BY public.ab_test_variants.id;


--
-- Name: ab_tests; Type: TABLE; Schema: public; Owner: content_creator_user
--

CREATE TABLE public.ab_tests (
    id integer NOT NULL,
    test_name character varying(200) NOT NULL,
    hypothesis text,
    variable_being_tested character varying(100) NOT NULL,
    insight_id integer,
    asset character varying(20),
    platform character varying(50),
    status public.teststatus,
    winning_variant_id integer,
    confidence_level double precision,
    improvement_percentage double precision,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    created_at timestamp without time zone
);


ALTER TABLE public.ab_tests OWNER TO content_creator_user;

--
-- Name: ab_tests_id_seq; Type: SEQUENCE; Schema: public; Owner: content_creator_user
--

CREATE SEQUENCE public.ab_tests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ab_tests_id_seq OWNER TO content_creator_user;

--
-- Name: ab_tests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: content_creator_user
--

ALTER SEQUENCE public.ab_tests_id_seq OWNED BY public.ab_tests.id;


--
-- Name: agent_logs; Type: TABLE; Schema: public; Owner: content_creator_user
--

CREATE TABLE public.agent_logs (
    id integer NOT NULL,
    "timestamp" timestamp without time zone,
    agent_name character varying(100) NOT NULL,
    action character varying(200) NOT NULL,
    status character varying(20),
    details json,
    error_message text,
    execution_time double precision,
    created_at timestamp without time zone
);


ALTER TABLE public.agent_logs OWNER TO content_creator_user;

--
-- Name: agent_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: content_creator_user
--

CREATE SEQUENCE public.agent_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.agent_logs_id_seq OWNER TO content_creator_user;

--
-- Name: agent_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: content_creator_user
--

ALTER SEQUENCE public.agent_logs_id_seq OWNED BY public.agent_logs.id;


--
-- Name: community_users; Type: TABLE; Schema: public; Owner: content_creator_user
--

CREATE TABLE public.community_users (
    id integer NOT NULL,
    twitter_id character varying(100),
    twitter_username character varying(100),
    telegram_id character varying(100),
    telegram_username character varying(100),
    discord_id character varying(100),
    discord_username character varying(100),
    email character varying(255),
    tier public.usertier NOT NULL,
    subscription_status character varying(20),
    total_interactions integer,
    last_interaction timestamp without time zone,
    engagement_score double precision,
    conversion_dm_sent boolean,
    conversion_dm_sent_at timestamp without time zone,
    conversion_dm_opened boolean,
    conversion_dm_clicked boolean,
    first_seen timestamp without time zone,
    converted_at timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.community_users OWNER TO content_creator_user;

--
-- Name: community_users_id_seq; Type: SEQUENCE; Schema: public; Owner: content_creator_user
--

CREATE SEQUENCE public.community_users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.community_users_id_seq OWNER TO content_creator_user;

--
-- Name: community_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: content_creator_user
--

ALTER SEQUENCE public.community_users_id_seq OWNED BY public.community_users.id;


--
-- Name: content_plans; Type: TABLE; Schema: public; Owner: content_creator_user
--

CREATE TABLE public.content_plans (
    id integer NOT NULL,
    "timestamp" timestamp without time zone,
    insight_id integer NOT NULL,
    platform character varying(50) NOT NULL,
    format public.contentformat NOT NULL,
    priority character varying(20),
    scheduled_for timestamp without time zone,
    status character varying(20),
    created_at timestamp without time zone
);


ALTER TABLE public.content_plans OWNER TO content_creator_user;

--
-- Name: content_plans_id_seq; Type: SEQUENCE; Schema: public; Owner: content_creator_user
--

CREATE SEQUENCE public.content_plans_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.content_plans_id_seq OWNER TO content_creator_user;

--
-- Name: content_plans_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: content_creator_user
--

ALTER SEQUENCE public.content_plans_id_seq OWNED BY public.content_plans.id;


--
-- Name: conversion_attempts; Type: TABLE; Schema: public; Owner: content_creator_user
--

CREATE TABLE public.conversion_attempts (
    id integer NOT NULL,
    user_id integer NOT NULL,
    platform character varying(20) NOT NULL,
    message_text text NOT NULL,
    discount_code character varying(50),
    discount_percentage integer,
    sent_at timestamp without time zone,
    opened_at timestamp without time zone,
    clicked_at timestamp without time zone,
    converted_at timestamp without time zone,
    status character varying(20),
    created_at timestamp without time zone
);


ALTER TABLE public.conversion_attempts OWNER TO content_creator_user;

--
-- Name: conversion_attempts_id_seq; Type: SEQUENCE; Schema: public; Owner: content_creator_user
--

CREATE SEQUENCE public.conversion_attempts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.conversion_attempts_id_seq OWNER TO content_creator_user;

--
-- Name: conversion_attempts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: content_creator_user
--

ALTER SEQUENCE public.conversion_attempts_id_seq OWNED BY public.conversion_attempts.id;


--
-- Name: exclusive_content; Type: TABLE; Schema: public; Owner: content_creator_user
--

CREATE TABLE public.exclusive_content (
    id integer NOT NULL,
    insight_id integer NOT NULL,
    content_text text NOT NULL,
    platform character varying(20) NOT NULL,
    min_tier_required public.usertier,
    published_at timestamp without time zone,
    channel_id character varying(100),
    message_id character varying(100),
    views integer,
    reactions integer,
    created_at timestamp without time zone
);


ALTER TABLE public.exclusive_content OWNER TO content_creator_user;

--
-- Name: exclusive_content_id_seq; Type: SEQUENCE; Schema: public; Owner: content_creator_user
--

CREATE SEQUENCE public.exclusive_content_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.exclusive_content_id_seq OWNER TO content_creator_user;

--
-- Name: exclusive_content_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: content_creator_user
--

ALTER SEQUENCE public.exclusive_content_id_seq OWNED BY public.exclusive_content.id;


--
-- Name: insights; Type: TABLE; Schema: public; Owner: content_creator_user
--

CREATE TABLE public.insights (
    id integer NOT NULL,
    "timestamp" timestamp without time zone,
    type public.insighttype NOT NULL,
    asset character varying(20) NOT NULL,
    confidence double precision NOT NULL,
    details json NOT NULL,
    supporting_data_ids json,
    is_published boolean,
    is_exclusive boolean,
    created_at timestamp without time zone
);


ALTER TABLE public.insights OWNER TO content_creator_user;

--
-- Name: insights_id_seq; Type: SEQUENCE; Schema: public; Owner: content_creator_user
--

CREATE SEQUENCE public.insights_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.insights_id_seq OWNER TO content_creator_user;

--
-- Name: insights_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: content_creator_user
--

ALTER SEQUENCE public.insights_id_seq OWNED BY public.insights.id;


--
-- Name: market_data; Type: TABLE; Schema: public; Owner: content_creator_user
--

CREATE TABLE public.market_data (
    id integer NOT NULL,
    "timestamp" timestamp without time zone,
    asset character varying(20) NOT NULL,
    price double precision NOT NULL,
    volume_24h double precision,
    price_change_24h double precision,
    market_cap double precision,
    raw_data json,
    created_at timestamp without time zone
);


ALTER TABLE public.market_data OWNER TO content_creator_user;

--
-- Name: market_data_id_seq; Type: SEQUENCE; Schema: public; Owner: content_creator_user
--

CREATE SEQUENCE public.market_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.market_data_id_seq OWNER TO content_creator_user;

--
-- Name: market_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: content_creator_user
--

ALTER SEQUENCE public.market_data_id_seq OWNED BY public.market_data.id;


--
-- Name: moderation_actions; Type: TABLE; Schema: public; Owner: content_creator_user
--

CREATE TABLE public.moderation_actions (
    id integer NOT NULL,
    user_id integer,
    platform_user_id character varying(100) NOT NULL,
    action_type character varying(50) NOT NULL,
    reason character varying(200) NOT NULL,
    platform character varying(20) NOT NULL,
    message_content text,
    channel_id character varying(100),
    automated boolean,
    agent_confidence double precision,
    duration_minutes integer,
    expires_at timestamp without time zone,
    "timestamp" timestamp without time zone,
    created_at timestamp without time zone
);


ALTER TABLE public.moderation_actions OWNER TO content_creator_user;

--
-- Name: moderation_actions_id_seq; Type: SEQUENCE; Schema: public; Owner: content_creator_user
--

CREATE SEQUENCE public.moderation_actions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.moderation_actions_id_seq OWNER TO content_creator_user;

--
-- Name: moderation_actions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: content_creator_user
--

ALTER SEQUENCE public.moderation_actions_id_seq OWNED BY public.moderation_actions.id;


--
-- Name: news_articles; Type: TABLE; Schema: public; Owner: content_creator_user
--

CREATE TABLE public.news_articles (
    id integer NOT NULL,
    title character varying(500) NOT NULL,
    url character varying(1000),
    source character varying(100),
    published_at timestamp without time zone,
    content text,
    summary text,
    sentiment_score double precision,
    mentioned_assets json,
    created_at timestamp without time zone
);


ALTER TABLE public.news_articles OWNER TO content_creator_user;

--
-- Name: news_articles_id_seq; Type: SEQUENCE; Schema: public; Owner: content_creator_user
--

CREATE SEQUENCE public.news_articles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.news_articles_id_seq OWNER TO content_creator_user;

--
-- Name: news_articles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: content_creator_user
--

ALTER SEQUENCE public.news_articles_id_seq OWNED BY public.news_articles.id;


--
-- Name: performance_snapshots; Type: TABLE; Schema: public; Owner: content_creator_user
--

CREATE TABLE public.performance_snapshots (
    id integer NOT NULL,
    snapshot_date timestamp without time zone,
    period_type character varying(20),
    content_published_count integer,
    avg_engagement_rate double precision,
    total_impressions integer,
    total_clicks integer,
    new_followers integer,
    total_followers integer,
    follower_growth_rate double precision,
    new_conversions integer,
    total_paying_members integer,
    revenue double precision,
    conversion_rate double precision,
    top_performing_format character varying(50),
    top_performing_asset character varying(20),
    top_performing_insight_type character varying(50),
    avg_insight_confidence double precision,
    insight_accuracy_rate double precision,
    created_at timestamp without time zone
);


ALTER TABLE public.performance_snapshots OWNER TO content_creator_user;

--
-- Name: performance_snapshots_id_seq; Type: SEQUENCE; Schema: public; Owner: content_creator_user
--

CREATE SEQUENCE public.performance_snapshots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.performance_snapshots_id_seq OWNER TO content_creator_user;

--
-- Name: performance_snapshots_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: content_creator_user
--

ALTER SEQUENCE public.performance_snapshots_id_seq OWNED BY public.performance_snapshots.id;


--
-- Name: published_content; Type: TABLE; Schema: public; Owner: content_creator_user
--

CREATE TABLE public.published_content (
    id integer NOT NULL,
    content_plan_id integer NOT NULL,
    platform character varying(50) NOT NULL,
    content_text text NOT NULL,
    media_urls json,
    post_url character varying(1000),
    post_id character varying(100),
    published_at timestamp without time zone,
    views integer,
    likes integer,
    comments integer,
    shares integer,
    engagement_rate double precision,
    ab_test_variant_id integer,
    created_at timestamp without time zone
);


ALTER TABLE public.published_content OWNER TO content_creator_user;

--
-- Name: published_content_id_seq; Type: SEQUENCE; Schema: public; Owner: content_creator_user
--

CREATE SEQUENCE public.published_content_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.published_content_id_seq OWNER TO content_creator_user;

--
-- Name: published_content_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: content_creator_user
--

ALTER SEQUENCE public.published_content_id_seq OWNED BY public.published_content.id;


--
-- Name: sentiment_data; Type: TABLE; Schema: public; Owner: content_creator_user
--

CREATE TABLE public.sentiment_data (
    id integer NOT NULL,
    "timestamp" timestamp without time zone,
    platform character varying(50),
    asset character varying(20),
    sentiment_score double precision,
    volume integer,
    influencer_sentiment double precision,
    raw_data json,
    created_at timestamp without time zone
);


ALTER TABLE public.sentiment_data OWNER TO content_creator_user;

--
-- Name: sentiment_data_id_seq; Type: SEQUENCE; Schema: public; Owner: content_creator_user
--

CREATE SEQUENCE public.sentiment_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sentiment_data_id_seq OWNER TO content_creator_user;

--
-- Name: sentiment_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: content_creator_user
--

ALTER SEQUENCE public.sentiment_data_id_seq OWNED BY public.sentiment_data.id;


--
-- Name: subscriptions; Type: TABLE; Schema: public; Owner: content_creator_user
--

CREATE TABLE public.subscriptions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    stripe_customer_id character varying(100),
    stripe_subscription_id character varying(100),
    stripe_payment_intent_id character varying(100),
    tier public.usertier NOT NULL,
    status character varying(20),
    amount double precision NOT NULL,
    currency character varying(3),
    current_period_start timestamp without time zone,
    current_period_end timestamp without time zone,
    trial_end timestamp without time zone,
    cancel_at_period_end boolean,
    cancelled_at timestamp without time zone,
    cancellation_reason text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.subscriptions OWNER TO content_creator_user;

--
-- Name: subscriptions_id_seq; Type: SEQUENCE; Schema: public; Owner: content_creator_user
--

CREATE SEQUENCE public.subscriptions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.subscriptions_id_seq OWNER TO content_creator_user;

--
-- Name: subscriptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: content_creator_user
--

ALTER SEQUENCE public.subscriptions_id_seq OWNED BY public.subscriptions.id;


--
-- Name: user_interactions; Type: TABLE; Schema: public; Owner: content_creator_user
--

CREATE TABLE public.user_interactions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    interaction_type character varying(50) NOT NULL,
    platform character varying(20) NOT NULL,
    content_id integer,
    interaction_metadata json,
    engagement_value double precision,
    "timestamp" timestamp without time zone
);


ALTER TABLE public.user_interactions OWNER TO content_creator_user;

--
-- Name: user_interactions_id_seq; Type: SEQUENCE; Schema: public; Owner: content_creator_user
--

CREATE SEQUENCE public.user_interactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_interactions_id_seq OWNER TO content_creator_user;

--
-- Name: user_interactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: content_creator_user
--

ALTER SEQUENCE public.user_interactions_id_seq OWNED BY public.user_interactions.id;


--
-- Name: ab_test_variants id; Type: DEFAULT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.ab_test_variants ALTER COLUMN id SET DEFAULT nextval('public.ab_test_variants_id_seq'::regclass);


--
-- Name: ab_tests id; Type: DEFAULT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.ab_tests ALTER COLUMN id SET DEFAULT nextval('public.ab_tests_id_seq'::regclass);


--
-- Name: agent_logs id; Type: DEFAULT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.agent_logs ALTER COLUMN id SET DEFAULT nextval('public.agent_logs_id_seq'::regclass);


--
-- Name: community_users id; Type: DEFAULT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.community_users ALTER COLUMN id SET DEFAULT nextval('public.community_users_id_seq'::regclass);


--
-- Name: content_plans id; Type: DEFAULT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.content_plans ALTER COLUMN id SET DEFAULT nextval('public.content_plans_id_seq'::regclass);


--
-- Name: conversion_attempts id; Type: DEFAULT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.conversion_attempts ALTER COLUMN id SET DEFAULT nextval('public.conversion_attempts_id_seq'::regclass);


--
-- Name: exclusive_content id; Type: DEFAULT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.exclusive_content ALTER COLUMN id SET DEFAULT nextval('public.exclusive_content_id_seq'::regclass);


--
-- Name: insights id; Type: DEFAULT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.insights ALTER COLUMN id SET DEFAULT nextval('public.insights_id_seq'::regclass);


--
-- Name: market_data id; Type: DEFAULT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.market_data ALTER COLUMN id SET DEFAULT nextval('public.market_data_id_seq'::regclass);


--
-- Name: moderation_actions id; Type: DEFAULT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.moderation_actions ALTER COLUMN id SET DEFAULT nextval('public.moderation_actions_id_seq'::regclass);


--
-- Name: news_articles id; Type: DEFAULT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.news_articles ALTER COLUMN id SET DEFAULT nextval('public.news_articles_id_seq'::regclass);


--
-- Name: performance_snapshots id; Type: DEFAULT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.performance_snapshots ALTER COLUMN id SET DEFAULT nextval('public.performance_snapshots_id_seq'::regclass);


--
-- Name: published_content id; Type: DEFAULT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.published_content ALTER COLUMN id SET DEFAULT nextval('public.published_content_id_seq'::regclass);


--
-- Name: sentiment_data id; Type: DEFAULT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.sentiment_data ALTER COLUMN id SET DEFAULT nextval('public.sentiment_data_id_seq'::regclass);


--
-- Name: subscriptions id; Type: DEFAULT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.subscriptions ALTER COLUMN id SET DEFAULT nextval('public.subscriptions_id_seq'::regclass);


--
-- Name: user_interactions id; Type: DEFAULT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.user_interactions ALTER COLUMN id SET DEFAULT nextval('public.user_interactions_id_seq'::regclass);


--
-- Data for Name: ab_test_variants; Type: TABLE DATA; Schema: public; Owner: content_creator_user
--

COPY public.ab_test_variants (id, test_id, variant_name, is_control, variant_config, impressions, clicks, engagement_count, conversion_count, click_through_rate, engagement_rate, conversion_rate, sample_size, created_at) FROM stdin;
\.


--
-- Data for Name: ab_tests; Type: TABLE DATA; Schema: public; Owner: content_creator_user
--

COPY public.ab_tests (id, test_name, hypothesis, variable_being_tested, insight_id, asset, platform, status, winning_variant_id, confidence_level, improvement_percentage, started_at, completed_at, created_at) FROM stdin;
\.


--
-- Data for Name: agent_logs; Type: TABLE DATA; Schema: public; Owner: content_creator_user
--

COPY public.agent_logs (id, "timestamp", agent_name, action, status, details, error_message, execution_time, created_at) FROM stdin;
\.


--
-- Data for Name: community_users; Type: TABLE DATA; Schema: public; Owner: content_creator_user
--

COPY public.community_users (id, twitter_id, twitter_username, telegram_id, telegram_username, discord_id, discord_username, email, tier, subscription_status, total_interactions, last_interaction, engagement_score, conversion_dm_sent, conversion_dm_sent_at, conversion_dm_opened, conversion_dm_clicked, first_seen, converted_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: content_plans; Type: TABLE DATA; Schema: public; Owner: content_creator_user
--

COPY public.content_plans (id, "timestamp", insight_id, platform, format, priority, scheduled_for, status, created_at) FROM stdin;
\.


--
-- Data for Name: conversion_attempts; Type: TABLE DATA; Schema: public; Owner: content_creator_user
--

COPY public.conversion_attempts (id, user_id, platform, message_text, discount_code, discount_percentage, sent_at, opened_at, clicked_at, converted_at, status, created_at) FROM stdin;
\.


--
-- Data for Name: exclusive_content; Type: TABLE DATA; Schema: public; Owner: content_creator_user
--

COPY public.exclusive_content (id, insight_id, content_text, platform, min_tier_required, published_at, channel_id, message_id, views, reactions, created_at) FROM stdin;
\.


--
-- Data for Name: insights; Type: TABLE DATA; Schema: public; Owner: content_creator_user
--

COPY public.insights (id, "timestamp", type, asset, confidence, details, supporting_data_ids, is_published, is_exclusive, created_at) FROM stdin;
\.


--
-- Data for Name: market_data; Type: TABLE DATA; Schema: public; Owner: content_creator_user
--

COPY public.market_data (id, "timestamp", asset, price, volume_24h, price_change_24h, market_cap, raw_data, created_at) FROM stdin;
\.


--
-- Data for Name: moderation_actions; Type: TABLE DATA; Schema: public; Owner: content_creator_user
--

COPY public.moderation_actions (id, user_id, platform_user_id, action_type, reason, platform, message_content, channel_id, automated, agent_confidence, duration_minutes, expires_at, "timestamp", created_at) FROM stdin;
\.


--
-- Data for Name: news_articles; Type: TABLE DATA; Schema: public; Owner: content_creator_user
--

COPY public.news_articles (id, title, url, source, published_at, content, summary, sentiment_score, mentioned_assets, created_at) FROM stdin;
\.


--
-- Data for Name: performance_snapshots; Type: TABLE DATA; Schema: public; Owner: content_creator_user
--

COPY public.performance_snapshots (id, snapshot_date, period_type, content_published_count, avg_engagement_rate, total_impressions, total_clicks, new_followers, total_followers, follower_growth_rate, new_conversions, total_paying_members, revenue, conversion_rate, top_performing_format, top_performing_asset, top_performing_insight_type, avg_insight_confidence, insight_accuracy_rate, created_at) FROM stdin;
\.


--
-- Data for Name: published_content; Type: TABLE DATA; Schema: public; Owner: content_creator_user
--

COPY public.published_content (id, content_plan_id, platform, content_text, media_urls, post_url, post_id, published_at, views, likes, comments, shares, engagement_rate, ab_test_variant_id, created_at) FROM stdin;
\.


--
-- Data for Name: sentiment_data; Type: TABLE DATA; Schema: public; Owner: content_creator_user
--

COPY public.sentiment_data (id, "timestamp", platform, asset, sentiment_score, volume, influencer_sentiment, raw_data, created_at) FROM stdin;
\.


--
-- Data for Name: subscriptions; Type: TABLE DATA; Schema: public; Owner: content_creator_user
--

COPY public.subscriptions (id, user_id, stripe_customer_id, stripe_subscription_id, stripe_payment_intent_id, tier, status, amount, currency, current_period_start, current_period_end, trial_end, cancel_at_period_end, cancelled_at, cancellation_reason, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: user_interactions; Type: TABLE DATA; Schema: public; Owner: content_creator_user
--

COPY public.user_interactions (id, user_id, interaction_type, platform, content_id, interaction_metadata, engagement_value, "timestamp") FROM stdin;
\.


--
-- Name: ab_test_variants_id_seq; Type: SEQUENCE SET; Schema: public; Owner: content_creator_user
--

SELECT pg_catalog.setval('public.ab_test_variants_id_seq', 1, false);


--
-- Name: ab_tests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: content_creator_user
--

SELECT pg_catalog.setval('public.ab_tests_id_seq', 1, false);


--
-- Name: agent_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: content_creator_user
--

SELECT pg_catalog.setval('public.agent_logs_id_seq', 1, false);


--
-- Name: community_users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: content_creator_user
--

SELECT pg_catalog.setval('public.community_users_id_seq', 1, false);


--
-- Name: content_plans_id_seq; Type: SEQUENCE SET; Schema: public; Owner: content_creator_user
--

SELECT pg_catalog.setval('public.content_plans_id_seq', 1, false);


--
-- Name: conversion_attempts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: content_creator_user
--

SELECT pg_catalog.setval('public.conversion_attempts_id_seq', 1, false);


--
-- Name: exclusive_content_id_seq; Type: SEQUENCE SET; Schema: public; Owner: content_creator_user
--

SELECT pg_catalog.setval('public.exclusive_content_id_seq', 1, false);


--
-- Name: insights_id_seq; Type: SEQUENCE SET; Schema: public; Owner: content_creator_user
--

SELECT pg_catalog.setval('public.insights_id_seq', 1, false);


--
-- Name: market_data_id_seq; Type: SEQUENCE SET; Schema: public; Owner: content_creator_user
--

SELECT pg_catalog.setval('public.market_data_id_seq', 1, false);


--
-- Name: moderation_actions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: content_creator_user
--

SELECT pg_catalog.setval('public.moderation_actions_id_seq', 1, false);


--
-- Name: news_articles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: content_creator_user
--

SELECT pg_catalog.setval('public.news_articles_id_seq', 1, false);


--
-- Name: performance_snapshots_id_seq; Type: SEQUENCE SET; Schema: public; Owner: content_creator_user
--

SELECT pg_catalog.setval('public.performance_snapshots_id_seq', 1, false);


--
-- Name: published_content_id_seq; Type: SEQUENCE SET; Schema: public; Owner: content_creator_user
--

SELECT pg_catalog.setval('public.published_content_id_seq', 1, false);


--
-- Name: sentiment_data_id_seq; Type: SEQUENCE SET; Schema: public; Owner: content_creator_user
--

SELECT pg_catalog.setval('public.sentiment_data_id_seq', 1, false);


--
-- Name: subscriptions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: content_creator_user
--

SELECT pg_catalog.setval('public.subscriptions_id_seq', 1, false);


--
-- Name: user_interactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: content_creator_user
--

SELECT pg_catalog.setval('public.user_interactions_id_seq', 1, false);


--
-- Name: ab_test_variants ab_test_variants_pkey; Type: CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.ab_test_variants
    ADD CONSTRAINT ab_test_variants_pkey PRIMARY KEY (id);


--
-- Name: ab_tests ab_tests_pkey; Type: CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.ab_tests
    ADD CONSTRAINT ab_tests_pkey PRIMARY KEY (id);


--
-- Name: agent_logs agent_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.agent_logs
    ADD CONSTRAINT agent_logs_pkey PRIMARY KEY (id);


--
-- Name: community_users community_users_pkey; Type: CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.community_users
    ADD CONSTRAINT community_users_pkey PRIMARY KEY (id);


--
-- Name: content_plans content_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.content_plans
    ADD CONSTRAINT content_plans_pkey PRIMARY KEY (id);


--
-- Name: conversion_attempts conversion_attempts_pkey; Type: CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.conversion_attempts
    ADD CONSTRAINT conversion_attempts_pkey PRIMARY KEY (id);


--
-- Name: exclusive_content exclusive_content_pkey; Type: CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.exclusive_content
    ADD CONSTRAINT exclusive_content_pkey PRIMARY KEY (id);


--
-- Name: insights insights_pkey; Type: CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.insights
    ADD CONSTRAINT insights_pkey PRIMARY KEY (id);


--
-- Name: market_data market_data_pkey; Type: CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.market_data
    ADD CONSTRAINT market_data_pkey PRIMARY KEY (id);


--
-- Name: moderation_actions moderation_actions_pkey; Type: CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.moderation_actions
    ADD CONSTRAINT moderation_actions_pkey PRIMARY KEY (id);


--
-- Name: news_articles news_articles_pkey; Type: CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.news_articles
    ADD CONSTRAINT news_articles_pkey PRIMARY KEY (id);


--
-- Name: news_articles news_articles_url_key; Type: CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.news_articles
    ADD CONSTRAINT news_articles_url_key UNIQUE (url);


--
-- Name: performance_snapshots performance_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.performance_snapshots
    ADD CONSTRAINT performance_snapshots_pkey PRIMARY KEY (id);


--
-- Name: published_content published_content_pkey; Type: CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.published_content
    ADD CONSTRAINT published_content_pkey PRIMARY KEY (id);


--
-- Name: sentiment_data sentiment_data_pkey; Type: CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.sentiment_data
    ADD CONSTRAINT sentiment_data_pkey PRIMARY KEY (id);


--
-- Name: subscriptions subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_pkey PRIMARY KEY (id);


--
-- Name: subscriptions subscriptions_stripe_customer_id_key; Type: CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_stripe_customer_id_key UNIQUE (stripe_customer_id);


--
-- Name: subscriptions subscriptions_stripe_subscription_id_key; Type: CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_stripe_subscription_id_key UNIQUE (stripe_subscription_id);


--
-- Name: user_interactions user_interactions_pkey; Type: CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.user_interactions
    ADD CONSTRAINT user_interactions_pkey PRIMARY KEY (id);


--
-- Name: ix_agent_logs_agent_name; Type: INDEX; Schema: public; Owner: content_creator_user
--

CREATE INDEX ix_agent_logs_agent_name ON public.agent_logs USING btree (agent_name);


--
-- Name: ix_agent_logs_timestamp; Type: INDEX; Schema: public; Owner: content_creator_user
--

CREATE INDEX ix_agent_logs_timestamp ON public.agent_logs USING btree ("timestamp");


--
-- Name: ix_community_users_discord_id; Type: INDEX; Schema: public; Owner: content_creator_user
--

CREATE UNIQUE INDEX ix_community_users_discord_id ON public.community_users USING btree (discord_id);


--
-- Name: ix_community_users_email; Type: INDEX; Schema: public; Owner: content_creator_user
--

CREATE UNIQUE INDEX ix_community_users_email ON public.community_users USING btree (email);


--
-- Name: ix_community_users_telegram_id; Type: INDEX; Schema: public; Owner: content_creator_user
--

CREATE UNIQUE INDEX ix_community_users_telegram_id ON public.community_users USING btree (telegram_id);


--
-- Name: ix_community_users_twitter_id; Type: INDEX; Schema: public; Owner: content_creator_user
--

CREATE UNIQUE INDEX ix_community_users_twitter_id ON public.community_users USING btree (twitter_id);


--
-- Name: ix_insights_asset; Type: INDEX; Schema: public; Owner: content_creator_user
--

CREATE INDEX ix_insights_asset ON public.insights USING btree (asset);


--
-- Name: ix_insights_timestamp; Type: INDEX; Schema: public; Owner: content_creator_user
--

CREATE INDEX ix_insights_timestamp ON public.insights USING btree ("timestamp");


--
-- Name: ix_insights_type; Type: INDEX; Schema: public; Owner: content_creator_user
--

CREATE INDEX ix_insights_type ON public.insights USING btree (type);


--
-- Name: ix_market_data_asset; Type: INDEX; Schema: public; Owner: content_creator_user
--

CREATE INDEX ix_market_data_asset ON public.market_data USING btree (asset);


--
-- Name: ix_market_data_timestamp; Type: INDEX; Schema: public; Owner: content_creator_user
--

CREATE INDEX ix_market_data_timestamp ON public.market_data USING btree ("timestamp");


--
-- Name: ix_moderation_actions_timestamp; Type: INDEX; Schema: public; Owner: content_creator_user
--

CREATE INDEX ix_moderation_actions_timestamp ON public.moderation_actions USING btree ("timestamp");


--
-- Name: ix_news_articles_published_at; Type: INDEX; Schema: public; Owner: content_creator_user
--

CREATE INDEX ix_news_articles_published_at ON public.news_articles USING btree (published_at);


--
-- Name: ix_performance_snapshots_snapshot_date; Type: INDEX; Schema: public; Owner: content_creator_user
--

CREATE INDEX ix_performance_snapshots_snapshot_date ON public.performance_snapshots USING btree (snapshot_date);


--
-- Name: ix_published_content_published_at; Type: INDEX; Schema: public; Owner: content_creator_user
--

CREATE INDEX ix_published_content_published_at ON public.published_content USING btree (published_at);


--
-- Name: ix_sentiment_data_asset; Type: INDEX; Schema: public; Owner: content_creator_user
--

CREATE INDEX ix_sentiment_data_asset ON public.sentiment_data USING btree (asset);


--
-- Name: ix_sentiment_data_timestamp; Type: INDEX; Schema: public; Owner: content_creator_user
--

CREATE INDEX ix_sentiment_data_timestamp ON public.sentiment_data USING btree ("timestamp");


--
-- Name: ix_user_interactions_timestamp; Type: INDEX; Schema: public; Owner: content_creator_user
--

CREATE INDEX ix_user_interactions_timestamp ON public.user_interactions USING btree ("timestamp");


--
-- Name: ab_test_variants ab_test_variants_test_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.ab_test_variants
    ADD CONSTRAINT ab_test_variants_test_id_fkey FOREIGN KEY (test_id) REFERENCES public.ab_tests(id);


--
-- Name: ab_tests ab_tests_insight_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.ab_tests
    ADD CONSTRAINT ab_tests_insight_id_fkey FOREIGN KEY (insight_id) REFERENCES public.insights(id);


--
-- Name: ab_tests ab_tests_winning_variant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.ab_tests
    ADD CONSTRAINT ab_tests_winning_variant_id_fkey FOREIGN KEY (winning_variant_id) REFERENCES public.ab_test_variants(id);


--
-- Name: content_plans content_plans_insight_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.content_plans
    ADD CONSTRAINT content_plans_insight_id_fkey FOREIGN KEY (insight_id) REFERENCES public.insights(id);


--
-- Name: conversion_attempts conversion_attempts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.conversion_attempts
    ADD CONSTRAINT conversion_attempts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.community_users(id);


--
-- Name: exclusive_content exclusive_content_insight_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.exclusive_content
    ADD CONSTRAINT exclusive_content_insight_id_fkey FOREIGN KEY (insight_id) REFERENCES public.insights(id);


--
-- Name: moderation_actions moderation_actions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.moderation_actions
    ADD CONSTRAINT moderation_actions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.community_users(id);


--
-- Name: published_content published_content_ab_test_variant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.published_content
    ADD CONSTRAINT published_content_ab_test_variant_id_fkey FOREIGN KEY (ab_test_variant_id) REFERENCES public.ab_test_variants(id);


--
-- Name: published_content published_content_content_plan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.published_content
    ADD CONSTRAINT published_content_content_plan_id_fkey FOREIGN KEY (content_plan_id) REFERENCES public.content_plans(id);


--
-- Name: subscriptions subscriptions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.community_users(id);


--
-- Name: user_interactions user_interactions_content_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.user_interactions
    ADD CONSTRAINT user_interactions_content_id_fkey FOREIGN KEY (content_id) REFERENCES public.published_content(id);


--
-- Name: user_interactions user_interactions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: content_creator_user
--

ALTER TABLE ONLY public.user_interactions
    ADD CONSTRAINT user_interactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.community_users(id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--

GRANT ALL ON SCHEMA public TO content_creator_user;


--
-- PostgreSQL database dump complete
--

