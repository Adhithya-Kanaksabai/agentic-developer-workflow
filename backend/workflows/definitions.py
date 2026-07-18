from engine.runtime import Workflow
from steps.planner import PlannerStep
from steps.builder import BuilderStep
from steps.reviewer import ReviewerStep

# Fixed V1 workflow definition
feature_v1_workflow = Workflow(
    name="Feature Development",
    steps=[
        PlannerStep(),
        BuilderStep(),
        ReviewerStep()
    ]
)
