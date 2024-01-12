resource "aws_ecr_repository" "app_ecr_repo" {
  name = "tele-bot-repo"
}

resource "aws_ecr_lifecycle_policy" "cleanup_policy" {
  repository = aws_ecr_repository.app_ecr_repo.name
  policy = jsonencode(
    {
      "rules" : [
        {
          "rulePriority" : 1,
          "description" : "Keep last 5 images",
          "selection" : {
            "tagStatus" : "any",
            "countType" : "imageCountMoreThan",
            "countNumber" : 5
          },
          "action" : {
            "type" : "expire"
          }
        }
      ]
  })
}
