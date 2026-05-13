# -*- coding: utf-8 -*-
"""
services/photo_illustration_service.py
---------------------------------------
사진 -> 그림일기 스타일 변환 서비스.

주요:
    - PhotoValidationResult : 검증 결과 dataclass (photo_validation_service 와 공유)
    - build_photo_illustration_prompt() : DALL-E 프롬프트 빌더

지원 케이스:
    - 강아지만 (dog_count >= 1, has_person=False)
    - 사람만 (dog_count == 0, has_person=True)
    - 강아지 + 사람 (dog_count >= 1, has_person=True)
    - 여러 마리 강아지 (dog_count >= 2) — 각각의 외형 묘사 사용
    - 여러 명의 사람 (person_count >= 2) — 각각의 외형 묘사 사용
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ── 검증 결과 dataclass ───────────────────────────────────────────────────────

@dataclass
class PhotoValidationResult:
    is_valid: bool
    rejection_reason: Optional[str]
    dog_count: int
    has_person: bool
    scene_description: str
    dog_visual_descriptions: list = field(default_factory=list)
    person_visual_description: str = ""


# ── DALL-E 프롬프트 빌더 ──────────────────────────────────────────────────────

def build_photo_illustration_prompt(
    dog_count: int,
    has_person: bool,
    scene_description: str,
    dog_visual_descriptions: list | None = None,
    person_visual_description: str = "",
    person_count: int = 1,
    person_visual_descriptions: list | None = None,
) -> str:
    """
    사진 분석 결과를 바탕으로 DALL-E 이미지 생성 프롬프트를 빌드합니다.

    Args:
        dog_count: 감지된 강아지 수 (0이면 강아지 없음)
        has_person: 사람 존재 여부
        scene_description: 장면 묘사
        dog_visual_descriptions: 강아지별 외형 묘사 리스트
        person_visual_description: 보호자 외형 묘사 (하위 호환용, 단일 문자열)
        person_count: 감지된 사람 수 (0이면 사람 없음)
        person_visual_descriptions: 사람별 외형 묘사 리스트
    """
    dog_visuals = dog_visual_descriptions or []
    person_visuals = person_visual_descriptions or ([person_visual_description] if person_visual_description else [])

    # ── 강아지 주어 & 구도 규칙 ─────────────────────────────────────────────
    if dog_count == 0:
        dog_subject = None
        dog_composition = None
    elif dog_count == 1:
        dog_subject = f"one adorable dog ({dog_visuals[0]})" if dog_visuals else "one adorable dog"
        dog_composition = (
            "the single dog must be the clear visual focal point, "
            "full body preferably visible, "
            "no duplicate dog, no mirror reflection of the dog"
        )
    elif dog_count == 2:
        if len(dog_visuals) >= 2:
            dog_subject = (
                f"two adorable dogs — "
                f"first dog: {dog_visuals[0]}, second dog: {dog_visuals[1]}"
            )
        elif len(dog_visuals) == 1:
            dog_subject = f"two adorable dogs — one of them: {dog_visuals[0]}"
        else:
            dog_subject = "two adorable dogs"
        dog_composition = (
            "both dogs must appear clearly in the same scene, "
            "render each dog as a visually distinct individual matching the descriptions above, "
            "no duplicate copies of the same dog pose, "
            "both dogs should be visible in full or near-full body"
        )
    else:
        if dog_visuals:
            desc_str = ", ".join(
                f"dog {i + 1}: {d}" for i, d in enumerate(dog_visuals[:dog_count])
            )
            dog_subject = f"{dog_count} adorable dogs — {desc_str}"
        else:
            dog_subject = f"{dog_count} adorable dogs"
        dog_composition = (
            f"all {dog_count} dogs must appear clearly in the same scene, "
            "render each dog as a visually distinct individual matching the descriptions above, "
            "arrange them naturally in a group — no duplicate poses, "
            "all dogs should be recognizable and clearly separated"
        )

    # ── 보호자/사람 묘사 ──────────────────────────────────────────────────────
    actual_person_count = person_count if person_count > 0 else (1 if has_person else 0)

    if actual_person_count == 0:
        person_line = "no humans appear in this scene"
    elif actual_person_count == 1:
        person_appearance = (
            f" ({person_visuals[0]})" if person_visuals else ""
        )
        person_line = (
            f"a person{person_appearance} appears in the scene, "
            "drawn in the same soft storybook illustration style — "
            "simple rounded storybook face, small dot eyes, tiny curved smile, soft oval face, "
            "East Asian appearance with black or dark brown eyes, "
            "person is secondary in visual weight compared to any dogs, "
            "no photorealistic human face, no detailed fingers, simplified hands"
        )
    else:
        if person_visuals:
            desc_str = ", ".join(
                f"person {i + 1}: {d}" for i, d in enumerate(person_visuals[:actual_person_count])
            )
            person_appearance = f" ({desc_str})"
        else:
            person_appearance = ""
        person_line = (
            f"{actual_person_count} people{person_appearance} appear in the scene, "
            "each drawn in the same soft storybook illustration style — "
            "simple rounded storybook faces, small dot eyes, tiny curved smiles, soft oval faces, "
            "East Asian appearance with black or dark brown eyes, "
            "people are secondary in visual weight compared to any dogs, "
            "no photorealistic human faces, no detailed fingers, simplified hands"
        )

    scene = scene_description.strip() if scene_description else "a warm everyday moment"

    # ── 공통 스타일 규칙 ───────────────────────────────────────────────────────
    texture_rules = (
        "STYLE: Korean-Japanese soft picture book illustration, "
        "soft gouache and colored pencil texture, matte hand-painted finish, "
        "calm pastel palette — sage green, powder blue, ivory white, soft neutral beige, "
        "soft natural daylight, gentle warm-neutral tone, "
        "avoid vivid saturation, avoid yellow cast, avoid sepia tone, "
        "avoid harsh contrast, avoid Western cartoon style"
    )

    quality_rules = (
        "premium polished children's picture book illustration, "
        "clean readable outlines, clear character silhouettes, "
        "finished professional composition, soft hand-painted texture, "
        "not photorealistic, not 3D render, not plastic, not hyper-detailed realism"
    )

    composition_rules = (
        "one single frozen moment in time — "
        "one continuous full-page illustration from a single camera view, "
        "no comic strip, no multi-panel, no split screen, no manga layout, "
        "no collage, no storyboard, no sequence of moments, "
        "no frames, no borders, no panel dividers, no boxed sections, no grid layout, "
        "balanced picture-book composition, "
        "no ghost images, no reflection animals, no duplicate characters"
    )

    location_suffix = (
        "Korean everyday setting if applicable, "
        "no Middle Eastern architecture, no mosque, no Arabic text"
    )

    # ── 주제에 따른 구성 ──────────────────────────────────────────────────────
    if dog_count > 0 and dog_subject:
        face_rules = (
            "each dog's face must have fully distinct readable features — "
            "two clear symmetrical eyes, one small clear nose, one tiny readable mouth, "
            "clean muzzle shape, clean ear shapes, clear facial silhouette, "
            "no blurry faces, no smudged faces, no melted or distorted features, "
            "no duplicated eyes, no extra limbs"
        )

        subject_line = f"Picture book illustration of {dog_subject} — {scene}"

        parts = [
            subject_line,
            dog_composition,
            person_line,
            face_rules,
            composition_rules,
            quality_rules,
            texture_rules,
            location_suffix,
            "no visible text or letters anywhere in the image",
        ]
    else:
        # 사람만 있는 경우
        face_rules = (
            "the person's face must have soft readable features — "
            "simple rounded storybook face, small dot eyes, tiny curved smile, "
            "East Asian appearance, clean facial silhouette, "
            "no blurry faces, no photorealistic details, no extra limbs"
        )

        if actual_person_count == 1:
            subject_line = f"Picture book illustration of a person — {scene}"
        else:
            subject_line = f"Picture book illustration of {actual_person_count} people — {scene}"

        parts = [
            subject_line,
            person_line,
            face_rules,
            composition_rules,
            quality_rules,
            texture_rules,
            location_suffix,
            "no visible text or letters anywhere in the image",
        ]

    return ", ".join(parts)
