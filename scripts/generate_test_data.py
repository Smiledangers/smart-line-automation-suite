#!/usr/bin/env python
"""
Test data generator for development and testing.
Generates realistic sample data for users, LINE users, scraping jobs, and AI conversations.
"""
import os
import sys
import random
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from faker import Faker

from app.core.config import settings
from app.models.user import User
from app.models.line_user import LINEUser
from app.models.scraping_job import ScrapingJob
from app.models.scraping_result import ScrapingResult
from app.models.ai_conversation import AIConversation, AIMessage

fake = Faker(["zh_TW", "en_US"])
Faker.seed(42)
random.seed(42)


def get_db_session():
    """Create database session."""
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()


def generate_users(session, count: int = 10) -> list:
    """Generate sample users."""
    print(f"Generating {count} users...")
    users = []
    
    for i in range(count):
        user = User(
            email=f"user{i+1}@example.com",
            username=f"user_{i+1}",
            full_name=fake.name(),
            is_active=True,
            is_superuser=False,
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
        )
        user.set_password("password123")
        session.add(user)
        users.append(user)
    
    session.commit()
    print(f"Created {len(users)} users")
    return users


def generate_line_users(session, users: list, count: int = 20) -> list:
    """Generate LINE users."""
    print(f"Generating {count} LINE users...")
    line_users = []
    
    for i in range(count):
        user = random.choice(users)
        line_user = LINEUser(
            line_user_id=f"U{random.randint(100000000000, 999999999999)}",
            user_id=user.id,
            display_name=fake.name(),
            picture_url=f"https://example.com/avatar/{i}.jpg",
            status_message=fake.sentence(),
            is_followed=True,
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
        )
        session.add(line_user)
        line_users.append(line_user)
    
    session.commit()
    print(f"Created {len(line_users)} LINE users")
    return line_users


def generate_scraping_jobs(session, users: list, count: int = 50) -> list:
    """Generate scraping jobs."""
    print(f"Generating {count} scraping jobs...")
    jobs = []
    sources = ["news", "ecommerce", "social", "blog", "forum"]
    statuses = ["pending", "running", "completed", "failed"]
    
    for i in range(count):
        user = random.choice(users)
        status = random.choices(
            statuses,
            weights=[30, 20, 40, 10]
        )[0]
        
        created_at = datetime.utcnow() - timedelta(days=random.randint(1, 30))
        
        job = ScrapingJob(
            user_id=user.id,
            url=f"https://example{i}.com/page",
            source=random.choice(sources),
            status=status,
            priority=random.randint(1, 5),
            created_at=created_at,
            started_at=created_at + timedelta(minutes=random.randint(1, 60)) if status in ["running", "completed", "failed"] else None,
            completed_at=created_at + timedelta(hours=random.randint(1, 5)) if status in ["completed", "failed"] else None,
            error_message=None if status != "failed" else fake.sentence(),
        )
        session.add(job)
        jobs.append(job)
        
        # Add some results for completed jobs
        if status == "completed" and random.random() > 0.5:
            result = ScrapingResult(
                job_id=job.id,
                url=job.url,
                title=f"Page Title {i}",
                content=fake.paragraph(),
                metadata={"scraped_by": "Botsaurus", "version": "1.0"},
                created_at=job.completed_at,
            )
            session.add(result)
    
    session.commit()
    print(f"Created {len(jobs)} scraping jobs")
    return jobs


def generate_ai_conversations(session, users: list, count: int = 30) -> list:
    """Generate AI conversations and messages."""
    print(f"Generating {count} AI conversations...")
    conversations = []
    
    for i in range(count):
        user = random.choice(users)
        created_at = datetime.utcnow() - timedelta(days=random.randint(1, 30))
        
        conv = AIConversation(
            user_id=user.id,
            title=f"Conversation {i+1}",
            model="gpt-4",
            is_active=random.choice([True, False]),
            created_at=created_at,
            updated_at=created_at + timedelta(hours=random.randint(1, 10)),
        )
        session.add(conv)
        conversations.append(conv)
        
        # Add messages to some conversations
        if random.random() > 0.3:
            num_messages = random.randint(2, 10)
            for j in range(num_messages):
                is_user = j % 2 == 0
                msg = AIMessage(
                    conversation_id=conv.id,
                    role="user" if is_user else "assistant",
                    content=fake.paragraph() if is_user else fake.sentence(),
                    created_at=created_at + timedelta(minutes=j * 5),
                )
                session.add(msg)
    
    session.commit()
    print(f"Created {len(conversations)} AI conversations")
    return conversations


def generate_all(session, counts: dict):
    """Generate all test data."""
    print("=" * 50)
    print("Generating test data...")
    print("=" * 50)
    
    users = generate_users(session, counts.get("users", 10))
    line_users = generate_line_users(session, users, counts.get("line_users", 20))
    jobs = generate_scraping_jobs(session, users, counts.get("scraping_jobs", 50))
    convs = generate_ai_conversations(session, users, counts.get("ai_conversations", 30))
    
    print("=" * 50)
    print("Test data generation complete!")
    print("=" * 50)
    print(f"Users: {len(users)}")
    print(f"LINE Users: {len(line_users)}")
    print(f"Scraping Jobs: {len(jobs)}")
    print(f"AI Conversations: {len(convs)}")


def clear_all_data(session):
    """Clear all data from tables."""
    print("Clearing all data...")
    session.query(AIMessage).delete()
    session.query(AIConversation).delete()
    session.query(ScrapingResult).delete()
    session.query(ScrapingJob).delete()
    session.query(LINEUser).delete()
    session.query(User).delete()
    session.commit()
    print("All data cleared!")


def main():
    parser = argparse.ArgumentParser(description="Generate test data for the application")
    parser.add_argument("--clear", action="store_true", help="Clear all data before generating")
    parser.add_argument("--users", type=int, default=10, help="Number of users to generate")
    parser.add_argument("--line-users", type=int, default=20, help="Number of LINE users to generate")
    parser.add_argument("--scraping-jobs", type=int, default=50, help="Number of scraping jobs to generate")
    parser.add_argument("--ai-conversations", type=int, default=30, help="Number of AI conversations to generate")
    
    args = parser.parse_args()
    
    session = get_db_session()
    
    try:
        if args.clear:
            clear_all_data(session)
        
        counts = {
            "users": args.users,
            "line_users": args.line_users,
            "scraping_jobs": args.scraping_jobs,
            "ai_conversations": args.ai_conversations,
        }
        generate_all(session, counts)
    finally:
        session.close()


if __name__ == "__main__":
    main()