from apps.content.services import ContentService


class ProjectContentService:
    @staticmethod
    def create_content_from_project(user, project, platform="LINKEDIN"):
        title = f"Case Study: How we built {project.title}"
        hook = f"We faced a major challenge: {project.problem or project.description}. Here is how we solved it using {project.technologies}."
        body = (
            f"**Project**: {project.title}\n\n"
            f"**Problem**: {project.problem}\n\n"
            f"**Solution**: {project.solution}\n\n"
            f"**Tech Stack**: {project.technologies}\n\n"
            f"GitHub Repo: {project.github_url}\n"
            f"Live Demo: {project.demo_url}"
        )
        cta = "What's your take on this architectural approach? Let's discuss in the comments!"

        content_item = ContentService.save_content_item(
            user=user,
            title=title,
            idea=f"Project Story derived from {project.title}",
            platform=platform,
            content_type=platform,
            hook=hook,
            body=body,
            cta=cta,
            status="DRAFT",
            change_reason=f"Generated from Project #{project.id}"
        )
        return content_item
