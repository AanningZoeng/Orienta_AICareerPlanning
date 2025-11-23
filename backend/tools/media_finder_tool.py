"""
Media finder tool for discovering educational videos and professional content.
Simulates searching YouTube, blogs, and professional interviews.
"""
from typing import Any, Dict, List
from spoon_ai.tools.base import BaseTool


class MediaFinderTool(BaseTool):
    """Tool for finding educational videos, blogs, and professional interviews."""
    
    name: str = "media_finder"
    description: str = "Finds YouTube channels, educational videos, blogs, and professional interviews related to careers"
    parameters: dict = {
        "type": "object",
        "properties": {
            "career_or_major": {
                "type": "string",
                "description": "Career title or major to find media content for"
            },
            "content_type": {
                "type": "string",
                "description": "Type of content: 'video', 'blog', 'interview', or 'all'",
                "enum": ["video", "blog", "interview", "all"]
            }
        },
        "required": ["career_or_major"]
    }
    
    async def execute(self, career_or_major: str, content_type: str = "all") -> Dict[str, Any]:
        """
        Simulate finding professional media content.
        
        In production, this would use YouTube API, blog search APIs, etc.
        For demo, we return realistic mock content.
        """
        # Mock media database
        media_database = {
            "Software Engineer": {
                "videos": [
                    {
                        "title": "A Day in the Life of a Software Engineer at Google",
                        "channel": "TechWithTim",
                        "url": "https://www.youtube.com/watch?v=example1",
                        "views": "2.5M"
                    },
                    {
                        "title": "How I Became a Software Engineer Without a CS Degree",
                        "channel": "ForrestKnight",
                        "url": "https://www.youtube.com/watch?v=example2",
                        "views": "1.8M"
                    }
                ],
                "blogs": [
                    {
                        "title": "The Complete Software Engineering Career Path Guide",
                        "author": "Martin Fowler",
                        "url": "https://martinfowler.com/career-guide",
                        "platform": "Personal Blog"
                    },
                    {
                        "title": "10 Years as a Software Engineer: Lessons Learned",
                        "author": "Dev.to Community",
                        "url": "https://dev.to/career-lessons",
                        "platform": "Dev.to"
                    }
                ],
                "interviews": [
                    {
                        "title": "Interview with Linus Torvalds on Linux Development",
                        "source": "TED Talks",
                        "url": "https://www.ted.com/talks/linus_torvalds",
                        "duration": "20 min"
                    }
                ]
            },
            "Marketing Manager": {
                "videos": [
                    {
                        "title": "Marketing Manager Career Path Explained",
                        "channel": "HubSpot Marketing",
                        "url": "https://www.youtube.com/watch?v=example3",
                        "views": "850K"
                    }
                ],
                "blogs": [
                    {
                        "title": "What It Takes to Be a Successful Marketing Manager",
                        "author": "Neil Patel",
                        "url": "https://neilpatel.com/blog/marketing-manager",
                        "platform": "NeilPatel.com"
                    }
                ],
                "interviews": [
                    {
                        "title": "CMO Roundtable: The Future of Marketing",
                        "source": "Marketing Week",
                        "url": "https://marketingweek.com/cmo-roundtable",
                        "duration": "35 min"
                    }
                ]
            },
            "Data Scientist": {
                "videos": [
                    {
                        "title": "How to Become a Data Scientist in 2024",
                        "channel": "DataCamp",
                        "url": "https://www.youtube.com/watch?v=example4",
                        "views": "1.2M"
                    }
                ],
                "blogs": [
                    {
                        "title": "My Journey from Analyst to Data Scientist",
                        "author": "Towards Data Science",
                        "url": "https://towardsdatascience.com/journey",
                        "platform": "Medium"
                    }
                ],
                "interviews": [
                    {
                        "title": "Andrew Ng on the Future of AI and Data Science",
                        "source": "Lex Fridman Podcast",
                        "url": "https://lexfridman.com/andrew-ng",
                        "duration": "2 hours"
                    }
                ]
            }
        }
        
        # Get or generate content
        if career_or_major in media_database:
            content = media_database[career_or_major]
        else:
            # Generate generic content
            content = {
                "videos": [
                    {
                        "title": f"Career Guide: {career_or_major}",
                        "channel": "Career Insights",
                        "url": "https://www.youtube.com/watch?v=example",
                        "views": "500K"
                    }
                ],
                "blogs": [
                    {
                        "title": f"Everything You Need to Know About {career_or_major}",
                        "author": "Career Blog",
                        "url": "https://careerblog.com/guide",
                        "platform": "Medium"
                    }
                ],
                "interviews": [
                    {
                        "title": f"Interview with a Successful {career_or_major}",
                        "source": "Professional Podcast",
                        "url": "https://podcast.com/interview",
                        "duration": "30 min"
                    }
                ]
            }
        
        # Filter by content type if specified
        if content_type != "all":
            filtered_content = {content_type + "s": content.get(content_type + "s", [])}
        else:
            filtered_content = content
        
        return {
            "success": True,
            "topic": career_or_major,
            "content": filtered_content,
            "total_items": sum(len(v) for v in filtered_content.values() if isinstance(v, list))
        }
