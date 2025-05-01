import sys
import os
import csv
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QComboBox, QSpinBox, QScrollArea, 
                             QFileDialog, QListWidget, QListWidgetItem, QGroupBox, 
                             QRadioButton, QButtonGroup, QSplitter, QFrame, QMessageBox,
                             QGridLayout, QTabWidget, QTextEdit)
from PyQt5.QtGui import QPixmap, QImage, QFont, QColor
from PyQt5.QtCore import Qt, QSize

class RubricItem:
    def __init__(self, id, title, max_points, definition, evaluation_scope, scoring_guidelines):
        self.id = id
        self.title = title
        self.max_points = max_points
        self.definition = definition
        self.evaluation_scope = evaluation_scope
        self.scoring_guidelines = scoring_guidelines
        self.score = 0

class DesignAnnotationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize app state
        self.images = []  # List of image file paths
        self.current_image_index = -1
        self.annotations = {}  # {image_name: {subcategory_id: score, ...}, ...}
        self.csv_filename = "annotations.csv"
        
        # Setup UI
        self.init_ui()
        
        # Create the rubric structure
        self.create_rubric()
        
        # Create the UI for the rubric
        self.create_rubric_ui()
        
        # Setup event handlers
        self.setup_event_handlers()
        
        # Update UI state
        self.update_ui_state()
        
    def init_ui(self):
        # Set window properties
        self.setWindowTitle("Design Assessment Annotation Tool")
        self.setGeometry(100, 100, 1600, 900)
        
        # Create main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        
        # Create splitter for resizable panels
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)
        
        # Left panel (sidebar)
        self.sidebar = QWidget()
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar.setMaximumWidth(350)
        self.sidebar.setMinimumWidth(250)
        
        # Add sidebar to splitter
        self.splitter.addWidget(self.sidebar)
        
        # Create right panel (main content)
        self.main_content = QWidget()
        self.main_content_layout = QVBoxLayout(self.main_content)
        
        # Add main content to splitter
        self.splitter.addWidget(self.main_content)
        
        # Folder selection section in sidebar
        self.folder_group = QGroupBox("Image Selection")
        self.folder_layout = QVBoxLayout(self.folder_group)
        
        self.folder_btn = QPushButton("Select Image Folder")
        self.folder_label = QLabel("No folder selected")
        self.folder_label.setWordWrap(True)
        
        self.folder_layout.addWidget(self.folder_btn)
        self.folder_layout.addWidget(self.folder_label)
        
        # CSV file selection
        self.csv_group = QGroupBox("Annotation File")
        self.csv_layout = QVBoxLayout(self.csv_group)
        
        self.load_csv_btn = QPushButton("Load Existing CSV")
        self.save_csv_btn = QPushButton("Save CSV As...")
        self.csv_label = QLabel(f"Current: {self.csv_filename}")
        self.csv_label.setWordWrap(True)
        
        self.csv_layout.addWidget(self.load_csv_btn)
        self.csv_layout.addWidget(self.save_csv_btn)
        self.csv_layout.addWidget(self.csv_label)
        
        # Image navigation
        self.nav_group = QGroupBox("Navigation")
        self.nav_layout = QGridLayout(self.nav_group)
        
        self.prev_btn = QPushButton("Previous")
        self.next_btn = QPushButton("Next")
        self.image_counter_label = QLabel("No images loaded")
        
        self.jump_label = QLabel("Jump to:")
        self.jump_spin = QSpinBox()
        self.jump_spin.setMinimum(1)
        self.jump_spin.setMaximum(1)
        self.jump_btn = QPushButton("Go")
        
        self.nav_layout.addWidget(self.prev_btn, 0, 0)
        self.nav_layout.addWidget(self.image_counter_label, 0, 1, 1, 2, Qt.AlignCenter)
        self.nav_layout.addWidget(self.next_btn, 0, 3)
        
        self.nav_layout.addWidget(self.jump_label, 1, 0)
        self.nav_layout.addWidget(self.jump_spin, 1, 1, 1, 2)
        self.nav_layout.addWidget(self.jump_btn, 1, 3)
        
        # Image list
        self.list_group = QGroupBox("Images")
        self.list_layout = QVBoxLayout(self.list_group)
        
        self.image_list = QListWidget()
        self.list_layout.addWidget(self.image_list)
        
        # Score summary
        self.summary_group = QGroupBox("Score Summary")
        self.summary_layout = QVBoxLayout(self.summary_group)
        
        self.score_breakdown = QTextEdit()
        self.score_breakdown.setReadOnly(True)
        self.score_breakdown.setMaximumHeight(150)
        
        self.total_score_label = QLabel("Total: 0/100")
        self.total_score_label.setAlignment(Qt.AlignRight)
        self.total_score_label.setFont(QFont("Arial", 12, QFont.Bold))
        
        self.save_annotation_btn = QPushButton("Save Annotation")
        self.save_annotation_btn.setEnabled(False)
        
        self.summary_layout.addWidget(self.score_breakdown)
        self.summary_layout.addWidget(self.total_score_label)
        self.summary_layout.addWidget(self.save_annotation_btn)
        
        # Add all groups to sidebar
        self.sidebar_layout.addWidget(self.folder_group)
        self.sidebar_layout.addWidget(self.csv_group)
        self.sidebar_layout.addWidget(self.nav_group)
        self.sidebar_layout.addWidget(self.list_group)
        self.sidebar_layout.addWidget(self.summary_group)
        
        # Main content - Image viewer
        self.image_viewer = QLabel()
        self.image_viewer.setAlignment(Qt.AlignCenter)
        self.image_viewer.setMinimumHeight(400)
        self.image_viewer.setStyleSheet("background-color: #eee; border: 1px solid #ddd;")
        
        # Create tabbed widget for rubric
        self.tabs = QTabWidget()
        
        # Rubric tab
        self.rubric_scroll = QScrollArea()
        self.rubric_scroll.setWidgetResizable(True)
        self.rubric_widget = QWidget()
        self.rubric_layout = QVBoxLayout(self.rubric_widget)
        self.rubric_scroll.setWidget(self.rubric_widget)
        
        self.tabs.addTab(self.rubric_scroll, "Assessment Rubric")
        
        # Preview tab (will show scoring guidelines legend)
        self.preview_widget = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_widget)
        
        # Add the scoring guidelines to the preview tab
        self.scoring_guide = QTextEdit()
        self.scoring_guide.setReadOnly(True)
        self.scoring_guide.setHtml("""
        <h2>Scoring Guidelines</h2>
        <p><strong>Score 90–100:</strong> Excellent design — Highly polished, well-aligned, and professional.</p>
        <p><strong>Score 80–89:</strong> Strong design — Generally cohesive and effective with minor issues.</p>
        <p><strong>Score 70–79:</strong> Needs refinement — Clear concept but notable execution or consistency flaws.</p>
        <p><strong>Score 60–69:</strong> Major improvement needed — Good intent, but structural or visual weaknesses.</p>
        <p><strong>Score below 60:</strong> Unsuccessful design — Lacks clarity, cohesion, or foundational principles.</p>
        """)
        
        self.preview_layout.addWidget(self.scoring_guide)
        
        self.tabs.addTab(self.preview_widget, "Scoring Guidelines")
        
        # Add elements to main content layout
        self.main_content_layout.addWidget(self.image_viewer)
        self.main_content_layout.addWidget(self.tabs)
        
        # Set the initial splitter sizes (35% sidebar, 65% main content)
        self.splitter.setSizes([350, 1250])

    def create_rubric(self):
        # Define the complete rubric structure
        self.rubric = [
            {
                "id": "whiteSpace",
                "title": "White Space Utilization",
                "max_points": 10,
                "subcategories": [
                    {
                        "id": "pageMargin",
                        "title": "Page Margin Assessment",
                        "max_points": 5,
                        "definition": "Assesses the presence and quality of margins around the content. Proper margins ensure breathing room and prevent crowding near the edges of the design.",
                        "evaluation_scope": [
                            "Measure the space between design elements and the canvas edges.",
                            "Margins should be consistent and proportional (e.g., ≥5% of canvas width/height).",
                            "Consider whether margins enhance overall clarity and composition."
                        ],
                        "scoring_guidelines": [
                            {"score": 5, "description": "Optimal, consistent margins framing the content effectively."},
                            {"score": 3, "description": "Acceptable margins; some inconsistency or room for improvement."},
                            {"score": 1, "description": "Minimal or irregular margins causing mild visual tension."},
                            {"score": 0, "description": "No discernible margins; content touches or crowds edges."}
                        ]
                    },
                    {
                        "id": "elementSpacing",
                        "title": "Element Spacing",
                        "max_points": 5,
                        "definition": "Evaluates the spacing between distinct groups of elements to ensure clear separation and logical information grouping.",
                        "evaluation_scope": [
                            "Check vertical and horizontal spacing between grouped elements.",
                            "Assess whether spacing helps convey content hierarchy.",
                            "Look for visual rhythm and proportionality."
                        ],
                        "scoring_guidelines": [
                            {"score": 5, "description": "Consistent, thoughtful spacing reinforcing structure and readability."},
                            {"score": 3, "description": "Functional spacing but slightly uneven or less polished."},
                            {"score": 1, "description": "Noticeable inconsistency or cramped grouping."},
                            {"score": 0, "description": "Elements appear crowded or cluttered."}
                        ]
                    }
                ]
            },
            {
                "id": "balance",
                "title": "Balance Assessment",
                "max_points": 15,
                "subcategories": [
                    {
                        "id": "spatialBalance",
                        "title": "Spatial Balance (Visual Weight Distribution)",
                        "max_points": 5,
                        "definition": "Assesses the overall spatial distribution of visual weight across the design. A well-balanced design feels stable and harmonious.",
                        "evaluation_scope": [
                            "Evaluate the center of visual mass relative to the canvas center.",
                            "Consider how element positions and densities contribute to perceived balance.",
                            "Large, bold, or high-contrast elements exert more \"weight.\"",
                            "Decorative background elements are only considered if they strongly influence visual balance."
                        ],
                        "scoring_guidelines": [
                            {"score": 5, "description": "Visual weight is evenly distributed; design feels centered or intentionally balanced."},
                            {"score": 3, "description": "Mostly balanced with small shifts or areas of mild heaviness."},
                            {"score": 1, "description": "Obvious imbalance; one side or region dominates uncomfortably."},
                            {"score": 0, "description": "Severely skewed layout causing immediate visual tension."}
                        ]
                    },
                    {
                        "id": "sizeHierarchy",
                        "title": "Size Hierarchy (All Elements)",
                        "max_points": 5,
                        "definition": "Assesses whether element sizes reflect their relative importance and contribute to effective hierarchy. This focuses on size across the entire design, not just local emphasis.",
                        "evaluation_scope": [
                            "Evaluate scaling between important and supporting elements.",
                            "Check proportionality and logic of visual sizing across sections.",
                            "Ignore emphasis created by color or placement—those are assessed elsewhere."
                        ],
                        "scoring_guidelines": [
                            {"score": 5, "description": "Strong, consistent size relationships reflecting clear hierarchy."},
                            {"score": 3, "description": "Mostly logical with slight inconsistencies."},
                            {"score": 1, "description": "Conflicting or unclear priority via sizing."},
                            {"score": 0, "description": "Arbitrary or confusing size usage."}
                        ]
                    },
                    {
                        "id": "typographyHierarchy",
                        "title": "Typography Hierarchy (Text Elements Only)",
                        "max_points": 5,
                        "definition": "Assesses whether text elements show logical hierarchy via size, weight, or spacing. This supports scannability and reading order.",
                        "evaluation_scope": [
                            "Evaluate consistency in size scaling (e.g., title > subtitle > paragraph).",
                            "Check spacing and font weight where relevant.",
                            "Do not evaluate aesthetic appropriateness or formatting quality here — that is assessed under Typography Effectiveness (Section 4)."
                        ],
                        "scoring_guidelines": [
                            {"score": 5, "description": "Clear, well-structured typographic hierarchy."},
                            {"score": 3, "description": "Reasonable variation with some room to improve."},
                            {"score": 1, "description": "Weak variation or confusing structure."},
                            {"score": 0, "description": "No visible hierarchy."}
                        ]
                    }
                ]
            },
            {
                "id": "alignment",
                "title": "Alignment",
                "max_points": 10,
                "subcategories": [
                    {
                        "id": "elementAlignment",
                        "title": "Element Alignment",
                        "max_points": 5,
                        "definition": "Assesses whether core content elements align with each other or a shared grid. Background visuals are ignored unless they affect layout clarity.",
                        "evaluation_scope": [
                            "Focus on horizontal and vertical alignment of text, images, and layout components.",
                            "Measure edge and center alignment."
                        ],
                        "scoring_guidelines": [
                            {"score": 5, "description": "Precise alignment and grid adherence."},
                            {"score": 3, "description": "Mostly aligned with some inconsistencies."},
                            {"score": 1, "description": "Misalignments reduce structure."},
                            {"score": 0, "description": "Layout feels scattered."}
                        ]
                    },
                    {
                        "id": "textAlignment",
                        "title": "Text Alignment",
                        "max_points": 5,
                        "definition": "Evaluates consistency in text alignment across paragraphs, titles, and sections.",
                        "evaluation_scope": [
                            "Compare justification and alignment style (left, center, right).",
                            "Check consistency within and across blocks.",
                            "This criterion focuses only on alignment style consistency. For spacing within text blocks, see Text Formatting (4.2)."
                        ],
                        "scoring_guidelines": [
                            {"score": 5, "description": "Fully consistent alignment."},
                            {"score": 3, "description": "Minor exceptions or slightly mixed styles."},
                            {"score": 1, "description": "Visibly inconsistent alignment."},
                            {"score": 0, "description": "No clear alignment pattern."}
                        ]
                    }
                ]
            },
            {
                "id": "typography",
                "title": "Typography Effectiveness",
                "max_points": 10,
                "subcategories": [
                    {
                        "id": "fontChoice",
                        "title": "Font Choice Appropriateness",
                        "max_points": 5,
                        "definition": "Assesses how well font selections match the tone and support readability.",
                        "evaluation_scope": [
                            "Consider typeface style, clarity, and appropriateness.",
                            "Look for harmony between fonts."
                        ],
                        "scoring_guidelines": [
                            {"score": 5, "description": "Fonts are excellent stylistic and functional fits."},
                            {"score": 3, "description": "Suitable but not optimal."},
                            {"score": 1, "description": "Questionable choices affect readability."},
                            {"score": 0, "description": "Inappropriate or hard to read fonts."}
                        ]
                    },
                    {
                        "id": "textFormatting",
                        "title": "Text Formatting",
                        "max_points": 5,
                        "definition": "Evaluates spacing, line height, and paragraph structure for readability.",
                        "evaluation_scope": [
                            "Check line spacing, word spacing, and alignment.",
                            "Evaluate typographic rhythm and cleanliness."
                        ],
                        "scoring_guidelines": [
                            {"score": 5, "description": "Clean, readable, and consistent formatting."},
                            {"score": 3, "description": "Adequate formatting with minor issues."},
                            {"score": 1, "description": "Formatting interferes with reading."},
                            {"score": 0, "description": "Poorly formatted or visually cluttered."}
                        ]
                    }
                ]
            },
            {
                "id": "color",
                "title": "Color",
                "max_points": 15,
                "subcategories": [
                    {
                        "id": "colorScheme",
                        "title": "Color Scheme Cohesiveness",
                        "max_points": 5,
                        "definition": "Assesses whether the color palette is unified, harmonious, and aesthetically pleasing.",
                        "evaluation_scope": [
                            "Consider palette use, tone, and balance.",
                            "Check for excessive or clashing colors."
                        ],
                        "scoring_guidelines": [
                            {"score": 5, "description": "Thoughtful and harmonious palette."},
                            {"score": 3, "description": "Mostly cohesive with minor mismatches."},
                            {"score": 1, "description": "Discordant or inconsistent."},
                            {"score": 0, "description": "Uncoordinated or random color use."}
                        ]
                    },
                    {
                        "id": "colorContrast",
                        "title": "Color Contrast",
                        "max_points": 5,
                        "definition": "Evaluates text and element visibility against background colors for readability and accessibility.",
                        "evaluation_scope": [
                            "Consider WCAG guidelines (e.g., ≥4.5:1 contrast ratio).",
                            "Look at text, icons, and buttons."
                        ],
                        "scoring_guidelines": [
                            {"score": 5, "description": "Excellent readability and contrast."},
                            {"score": 3, "description": "Acceptable, but could be improved."},
                            {"score": 1, "description": "Some elements are hard to read."},
                            {"score": 0, "description": "Low contrast impairs usability."}
                        ]
                    },
                    {
                        "id": "colorApplication",
                        "title": "Color Application (with Semantic Use)",
                        "max_points": 5,
                        "definition": "Assesses how color is used to support structure, hierarchy, and meaning (e.g., using red for errors or consistent hues for sections).",
                        "evaluation_scope": [
                            "Evaluate how color enhances clarity, draws attention, and supports design goals.",
                            "Check if color communicates relationships or states."
                        ],
                        "scoring_guidelines": [
                            {"score": 5, "description": "Purposeful and effective color usage."},
                            {"score": 3, "description": "Mostly appropriate, minor mismatches."},
                            {"score": 1, "description": "Inconsistent or confusing."},
                            {"score": 0, "description": "Actively misleading or unclear."}
                        ]
                    }
                ]
            },
            {
                "id": "consistency",
                "title": "Similarity & Consistency",
                "max_points": 10,
                "subcategories": [
                    {
                        "id": "elementConsistency",
                        "title": "Consistency in Element Types",
                        "max_points": 5,
                        "definition": "Assesses whether elements of the same type (e.g., all titles or buttons) share consistent styles across the design.",
                        "evaluation_scope": [
                            "Compare font, color, size, padding, and spacing within same-type elements."
                        ],
                        "scoring_guidelines": [
                            {"score": 5, "description": "All same-type elements are visually consistent."},
                            {"score": 3, "description": "Minor inconsistencies without significant disruption."},
                            {"score": 1, "description": "Noticeable inconsistencies that disrupt clarity."},
                            {"score": 0, "description": "No visual consistency among same-type elements."}
                        ]
                    },
                    {
                        "id": "relatedGroups",
                        "title": "Related Groups",
                        "max_points": 5,
                        "definition": "Evaluates whether visually or contextually related groups share cohesive styling to indicate connection.",
                        "evaluation_scope": [
                            "Assess color, font, background, or layout used within related sections.",
                            "Look for grouped elements that visually \"belong together.\""
                        ],
                        "scoring_guidelines": [
                            {"score": 5, "description": "Strong coordination within groups."},
                            {"score": 3, "description": "Some stylistic unity with mismatches."},
                            {"score": 1, "description": "Weak grouping or unclear connections."},
                            {"score": 0, "description": "Groups are visually disjointed."}
                        ]
                    }
                ]
            },
            {
                "id": "informationFlow",
                "title": "Information Flow & Emphasis",
                "max_points": 10,
                "subcategories": [
                    {
                        "id": "hierarchicalFlow",
                        "title": "Hierarchical Flow & Layout Logic",
                        "max_points": 5,
                        "definition": "Assesses whether the layout presents information in a clear and intuitive order.",
                        "evaluation_scope": [
                            "Examine grouping, scanning paths, and reading flow.",
                            "Evaluate information clarity and structure."
                        ],
                        "scoring_guidelines": [
                            {"score": 5, "description": "Seamless, logical flow."},
                            {"score": 3, "description": "Mostly effective, minor friction."},
                            {"score": 1, "description": "Confusing or inconsistent order."},
                            {"score": 0, "description": "No clear information structure."}
                        ]
                    },
                    {
                        "id": "emphasisTechniques",
                        "title": "Emphasis Techniques",
                        "max_points": 5,
                        "definition": "Assesses how visual cues—including size, color, position, and whitespace—guide the viewer's focus. This includes local emphasis that may complement, but not replace, global hierarchy.",
                        "evaluation_scope": [
                            "Look at callouts, titles, CTAs, and key visuals.",
                            "Consider combined use of multiple emphasis methods.",
                            "Focus on the success of attention-guiding execution rather than the correctness of size or color logic in isolation."
                        ],
                        "scoring_guidelines": [
                            {"score": 5, "description": "Masterful, intentional emphasis throughout."},
                            {"score": 3, "description": "Adequate and clear, but not refined."},
                            {"score": 1, "description": "Weak or inconsistent."},
                            {"score": 0, "description": "No clear visual priority."}
                        ]
                    }
                ]
            },
            {
                "id": "brandAdherence",
                "title": "Brand Adherence",
                "max_points": 15,
                "subcategories": [
                    {
                        "id": "colorBrand",
                        "title": "Color Brand Alignment",
                        "max_points": 5,
                        "definition": "Assesses whether color choices align with the intended brand identity, theme, or industry context.",
                        "evaluation_scope": [
                            "Evaluate brand palette usage, saturation, and consistency with brand tone.",
                            "Consider how color choices reflect personality and professionalism."
                        ],
                        "scoring_guidelines": [
                            {"score": 5, "description": "Color usage perfectly matches brand/tone."},
                            {"score": 3, "description": "Mostly aligned with minor mismatches."},
                            {"score": 1, "description": "Somewhat off-brand."},
                            {"score": 0, "description": "Clashes with brand or feels out of place."}
                        ]
                    },
                    {
                        "id": "typographyBrand",
                        "title": "Typography Brand Alignment",
                        "max_points": 5,
                        "definition": "Assesses whether the typography (font family, weight, and hierarchy) reflects the visual tone and character of the brand.",
                        "evaluation_scope": [
                            "Examine typeface consistency with brand standards or design system.",
                            "Assess if typographic tone (modern, playful, serious, etc.) matches the intended voice.",
                            "Score this only based on alignment with brand guidelines or intended personality — not overall legibility or formatting quality (see Section 4)."
                        ],
                        "scoring_guidelines": [
                            {"score": 5, "description": "Typeface choices align perfectly with brand identity."},
                            {"score": 3, "description": "Mostly aligned with some deviation."},
                            {"score": 1, "description": "Poor typeface fit for tone or usage."},
                            {"score": 0, "description": "Typography contradicts brand voice."}
                        ]
                    },
                    {
                        "id": "visualStyling",
                        "title": "Visual Styling Brand Alignment",
                        "max_points": 5,
                        "definition": "Evaluates whether the overall design style—such as iconography, illustration, button style, stroke weight, and shapes—matches the brand's visual system.",
                        "evaluation_scope": [
                            "Assess icon, illustration, and shape styles (e.g., minimal, skeuomorphic, playful).",
                            "Evaluate how well styling aligns with brand intent (e.g., tech startup vs. children's book)."
                        ],
                        "scoring_guidelines": [
                            {"score": 5, "description": "Visual styling is fully cohesive with brand."},
                            {"score": 3, "description": "Mostly aligned with minor style mismatches."},
                            {"score": 1, "description": "Elements feel somewhat inconsistent with brand."},
                            {"score": 0, "description": "Style contradicts brand system or tone."}
                        ]
                    }
                ]
            },
            {
                "id": "holisticImpact",
                "title": "Holistic Design Impact",
                "max_points": 10,
                "subcategories": [
                    {
                        "id": "visualCohesion",
                        "title": "Visual Cohesion & Appeal",
                        "max_points": 5,
                        "definition": "Assesses the overall visual harmony and polish of the design.",
                        "evaluation_scope": [
                            "Judge aesthetic unity, balance, and engagement.",
                            "Consider refinement and professionalism."
                        ],
                        "scoring_guidelines": [
                            {"score": 5, "description": "Exceptionally cohesive and polished."},
                            {"score": 3, "description": "Pleasant but not fully refined."},
                            {"score": 1, "description": "Disjointed or rough."},
                            {"score": 0, "description": "Unappealing or chaotic."}
                        ]
                    },
                    {
                        "id": "communicationEffectiveness",
                        "title": "Communication Effectiveness",
                        "max_points": 5,
                        "definition": "Evaluates whether the design clearly conveys its intended message or function.",
                        "evaluation_scope": [
                            "Check for clarity, alignment with goals, and user resonance.",
                            "Look at tone, readability, and impact."
                        ],
                        "scoring_guidelines": [
                            {"score": 5, "description": "Clear, effective, and impactful communication."},
                            {"score": 3, "description": "Message is mostly understood."},
                            {"score": 1, "description": "Partially unclear or ineffective."},
                            {"score": 0, "description": "Confusing or contradicts the goal."}
                        ]
                    }
                ]
            }
        ]
        
        # Build the subcategory mapping for easy access
        self.subcategory_map = {}
        for category in self.rubric:
            for subcategory in category["subcategories"]:
                self.subcategory_map[subcategory["id"]] = subcategory

    def create_rubric_ui(self):
        # Create the UI components for each rubric category
        for category_index, category in enumerate(self.rubric):
            # Create category group box
            category_box = QGroupBox(f"{category['title']} (0/{category['max_points']})")
            category_box.setObjectName(f"category_{category['id']}")
            category_layout = QVBoxLayout(category_box)
            
            # For each subcategory
            for subcategory in category["subcategories"]:
                # Create subcategory section
                subcategory_frame = QFrame()
                subcategory_frame.setFrameShape(QFrame.StyledPanel)
                subcategory_frame.setObjectName(f"subcategory_{subcategory['id']}")
                subcategory_layout = QVBoxLayout(subcategory_frame)
                
                # Subcategory title
                title_layout = QHBoxLayout()
                title_label = QLabel(f"<b>{subcategory['title']}</b> (0/{subcategory['max_points']} points)")
                title_label.setObjectName(f"title_{subcategory['id']}")
                title_layout.addWidget(title_label)
                subcategory_layout.addLayout(title_layout)
                
                # Definition
                definition_label = QLabel(subcategory["definition"])
                definition_label.setWordWrap(True)
                definition_label.setStyleSheet("font-style: italic; color: #555;")
                subcategory_layout.addWidget(definition_label)
                
                # Evaluation scope
                scope_label = QLabel("<b>Evaluation Scope:</b>")
                subcategory_layout.addWidget(scope_label)
                
                for scope_item in subcategory["evaluation_scope"]:
                    item_label = QLabel(f"• {scope_item}")
                    item_label.setWordWrap(True)
                    subcategory_layout.addWidget(item_label)
                
                # Scoring guidelines
                guidelines_label = QLabel("<b>Scoring Guidelines:</b>")
                subcategory_layout.addWidget(guidelines_label)
                
                for guideline in subcategory["scoring_guidelines"]:
                    guideline_label = QLabel(f"• <b>{guideline['score']}:</b> {guideline['description']}")
                    guideline_label.setWordWrap(True)
                    subcategory_layout.addWidget(guideline_label)
                
                # Score selection
                score_layout = QHBoxLayout()
                score_label = QLabel("Score:")
                score_layout.addWidget(score_label)
                
                # Create button group for radio buttons
                button_group = QButtonGroup(self)
                button_group.setObjectName(f"group_{subcategory['id']}")
                
                # Add radio buttons for each possible score
                for score in range(subcategory["max_points"] + 1):
                    radio = QRadioButton(str(score))
                    radio.setObjectName(f"score_{subcategory['id']}_{score}")
                    button_group.addButton(radio, score)
                    score_layout.addWidget(radio)
                
                # Store the button group in the class for easy access later
                setattr(self, f"group_{subcategory['id']}", button_group)
                
                # Connect button group to score changed function
                button_group.buttonClicked.connect(self.on_score_changed)
                
                subcategory_layout.addLayout(score_layout)
                
                # Add a separator line
                if subcategory != category["subcategories"][-1]:
                    line = QFrame()
                    line.setFrameShape(QFrame.HLine)
                    line.setFrameShadow(QFrame.Sunken)
                    subcategory_layout.addWidget(line)
                
                # Add subcategory to category
                category_layout.addWidget(subcategory_frame)
            
            # Add category to rubric layout
            self.rubric_layout.addWidget(category_box)
        
        # Add stretch to the end to push everything up
        self.rubric_layout.addStretch()

    def setup_event_handlers(self):
        # Folder selection
        self.folder_btn.clicked.connect(self.select_folder)
        
        # CSV file operations
        self.load_csv_btn.clicked.connect(self.load_csv)
        self.save_csv_btn.clicked.connect(self.save_csv_as)
        
        # Navigation
        self.prev_btn.clicked.connect(self.navigate_previous)
        self.next_btn.clicked.connect(self.navigate_next)
        self.jump_btn.clicked.connect(self.jump_to_image)
        
        # Save annotation
        self.save_annotation_btn.clicked.connect(self.save_annotation)
        
        # Image list selection
        self.image_list.itemClicked.connect(self.on_image_selected)

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if folder_path:
            # Get image files from folder
            image_files = []
            for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                image_files.extend(
                    [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                     if f.lower().endswith(ext)]
                )
            
            if not image_files:
                QMessageBox.warning(self, "No Images", "No image files found in the selected folder.")
                return
            
            # Sort images by name
            image_files.sort()
            
            # Update state
            self.images = image_files
            self.current_image_index = 0
            
            # Update UI
            self.folder_label.setText(folder_path)
            self.update_image_list()
            self.load_current_image()
            self.update_ui_state()

    def load_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Annotations CSV", "", "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', newline='') as csvfile:
                    reader = csv.DictReader(csvfile)
                    
                    # Reset annotations
                    self.annotations = {}
                    
                    for row in reader:
                        if 'Image' not in row:
                            QMessageBox.warning(
                                self, "Invalid CSV", "CSV file does not have an 'Image' column."
                            )
                            return
                        
                        image_name = row['Image']
                        scores = {}
                        
                        # Extract scores for each subcategory
                        for subcategory_id in self.subcategory_map.keys():
                            if subcategory_id in row:
                                try:
                                    scores[subcategory_id] = int(row[subcategory_id])
                                except ValueError:
                                    scores[subcategory_id] = 0
                        
                        # Store annotation
                        self.annotations[os.path.basename(image_name)] = scores
                    
                    # Update CSV filename
                    self.csv_filename = os.path.basename(file_path)
                    self.csv_label.setText(f"Current: {self.csv_filename}")
                    
                    # Update image list to show annotated status
                    self.update_image_list()
                    
                    # Load annotation for current image if exists
                    if self.current_image_index >= 0 and self.images:
                        current_image_name = os.path.basename(self.images[self.current_image_index])
                        self.load_annotation(current_image_name)
                    
                    QMessageBox.information(
                        self, "CSV Loaded", f"Loaded annotations for {len(self.annotations)} images."
                    )
            
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load CSV: {str(e)}")

    def save_csv_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Annotations As", self.csv_filename, "CSV Files (*.csv)"
        )
        
        if file_path:
            self.csv_filename = os.path.basename(file_path)
            self.csv_label.setText(f"Current: {self.csv_filename}")
            self.export_to_csv(file_path)

    def export_to_csv(self, file_path):
        try:
            # Create headers
            headers = ['Image']
            
            for category in self.rubric:
                for subcategory in category["subcategories"]:
                    headers.append(subcategory["id"])
            
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                
                for image_name, scores in self.annotations.items():
                    row = {'Image': image_name}
                    row.update(scores)
                    writer.writerow(row)
            
            QMessageBox.information(
                self, "Export Successful", f"Annotations exported to {file_path}"
            )
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export CSV: {str(e)}")

    def update_image_list(self):
        # Clear the list
        self.image_list.clear()
        
        # Add each image to the list
        for i, image_path in enumerate(self.images):
            image_name = os.path.basename(image_path)
            
            # Create list item
            item = QListWidgetItem(f"{i+1}. {image_name}")
            
            # Set font to bold if it's the current image
            if i == self.current_image_index:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            
            # Set background color if it's annotated
            if image_name in self.annotations:
                item.setBackground(QColor(220, 255, 220))  # Light green
            
            # Add to list
            self.image_list.addItem(item)
        
        # Set max value for jump spinner
        self.jump_spin.setMaximum(max(1, len(self.images)))

    def load_current_image(self):
        if not self.images or self.current_image_index < 0:
            self.image_viewer.setText("No images loaded")
            self.image_counter_label.setText("No images loaded")
            return
        
        # Get current image path
        image_path = self.images[self.current_image_index]
        image_name = os.path.basename(image_path)
        
        # Load image
        pixmap = QPixmap(image_path)
        
        # Scale pixmap if too large
        max_width = self.image_viewer.width() - 20
        max_height = self.image_viewer.height() - 20
        
        if pixmap.width() > max_width or pixmap.height() > max_height:
            pixmap = pixmap.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # Set the image
        self.image_viewer.setPixmap(pixmap)
        
        # Update counter
        self.image_counter_label.setText(f"Image {self.current_image_index + 1} of {len(self.images)}")
        
        # Load annotation if exists
        self.load_annotation(image_name)
        
        # Update image list to highlight current image
        self.update_image_list()

    def load_annotation(self, image_name):
        # Reset all scores first
        self.reset_scores()
        
        # If there's annotation for this image, load it
        if image_name in self.annotations:
            scores = self.annotations[image_name]
            
            # Set scores in the UI
            for subcategory_id, score in scores.items():
                # Get the button group
                button_group = getattr(self, f"group_{subcategory_id}", None)
                if button_group:
                    # Find the button with this score and check it
                    button = button_group.button(score)
                    if button:
                        button.setChecked(True)
            
            # Update all scores
            self.update_scores()

    def reset_scores(self):
        # Uncheck all radio buttons
        for category in self.rubric:
            for subcategory in category["subcategories"]:
                button_group = getattr(self, f"group_{subcategory['id']}", None)
                if button_group:
                    button_group.setExclusive(False)
                    for button in button_group.buttons():
                        button.setChecked(False)
                    button_group.setExclusive(True)
        
        # Reset category titles
        for category in self.rubric:
            category_box = self.findChild(QGroupBox, f"category_{category['id']}")
            if category_box:
                category_box.setTitle(f"{category['title']} (0/{category['max_points']})")
        
        # Reset subcategory titles
        for subcategory_id in self.subcategory_map:
            subcategory = self.subcategory_map[subcategory_id]
            title_label = self.findChild(QLabel, f"title_{subcategory_id}")
            if title_label:
                title_label.setText(f"<b>{subcategory['title']}</b> (0/{subcategory['max_points']} points)")
        
        # Reset total score
        self.total_score_label.setText("Total: 0/100")
        
        # Reset score breakdown
        self.update_score_breakdown()

    def on_score_changed(self, button):
        if not self.images or self.current_image_index < 0:
            return
        
        # Update scores
        self.update_scores()
        
        # Enable save button
        self.save_annotation_btn.setEnabled(True)

    def update_scores(self):
        total_score = 0
        
        # Calculate scores for each category
        for category in self.rubric:
            category_score = 0
            
            for subcategory in category["subcategories"]:
                button_group = getattr(self, f"group_{subcategory['id']}", None)
                if button_group:
                    checked_button = button_group.checkedButton()
                    if checked_button:
                        score = button_group.id(checked_button)
                        category_score += score
                        
                        # Update subcategory title
                        title_label = self.findChild(QLabel, f"title_{subcategory['id']}")
                        if title_label:
                            title_label.setText(
                                f"<b>{subcategory['title']}</b> ({score}/{subcategory['max_points']} points)"
                            )
            
            # Update category title
            category_box = self.findChild(QGroupBox, f"category_{category['id']}")
            if category_box:
                category_box.setTitle(f"{category['title']} ({category_score}/{category['max_points']})")
            
            total_score += category_score
        
        # Update total score
        self.total_score_label.setText(f"Total: {total_score}/100")
        
        # Update score breakdown
        self.update_score_breakdown(total_score)

    def update_score_breakdown(self, total_score=0):
        # Create breakdown text
        html = "<h3>Score Breakdown</h3>"
        
        for category in self.rubric:
            category_score = 0
            
            for subcategory in category["subcategories"]:
                button_group = getattr(self, f"group_{subcategory['id']}", None)
                if button_group:
                    checked_button = button_group.checkedButton()
                    if checked_button:
                        category_score += button_group.id(checked_button)
            
            html += f"<p><b>{category['title']}:</b> {category_score}/{category['max_points']}</p>"
        
        # Add rating based on total score
        if total_score >= 90:
            rating = "Excellent design — Highly polished, well-aligned, and professional."
        elif total_score >= 80:
            rating = "Strong design — Generally cohesive and effective with minor issues."
        elif total_score >= 70:
            rating = "Needs refinement — Clear concept but notable execution or consistency flaws."
        elif total_score >= 60:
            rating = "Major improvement needed — Good intent, but structural or visual weaknesses."
        else:
            rating = "Unsuccessful design — Lacks clarity, cohesion, or foundational principles."
        
        html += f"<p><b>Rating:</b> {rating}</p>"
        
        # Set the text
        self.score_breakdown.setHtml(html)

    def save_annotation(self):
        if not self.images or self.current_image_index < 0:
            return
        
        # Get current image name
        image_name = os.path.basename(self.images[self.current_image_index])
        
        # Collect scores
        scores = {}
        
        for category in self.rubric:
            for subcategory in category["subcategories"]:
                button_group = getattr(self, f"group_{subcategory['id']}", None)
                if button_group:
                    checked_button = button_group.checkedButton()
                    if checked_button:
                        scores[subcategory["id"]] = button_group.id(checked_button)
                    else:
                        scores[subcategory["id"]] = 0
        
        # Save to annotations
        self.annotations[image_name] = scores
        
        # Update image list
        self.update_image_list()
        
        # Automatically save to CSV file if it exists
        if self.csv_filename:
            self.export_to_csv(self.csv_filename)
        
        # Disable save button
        self.save_annotation_btn.setEnabled(False)
        
        # Show confirmation
        QMessageBox.information(self, "Saved", f"Annotation saved for {image_name}")

    def navigate_previous(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.load_current_image()
            self.update_ui_state()

    def navigate_next(self):
        if self.current_image_index < len(self.images) - 1:
            self.current_image_index += 1
            self.load_current_image()
            self.update_ui_state()

    def jump_to_image(self):
        index = self.jump_spin.value() - 1
        if 0 <= index < len(self.images):
            self.current_image_index = index
            self.load_current_image()
            self.update_ui_state()

    def on_image_selected(self, item):
        # Get the index from the item text (format: "1. image.jpg")
        index_str = item.text().split('.')[0]
        try:
            index = int(index_str) - 1
            if 0 <= index < len(self.images):
                self.current_image_index = index
                self.load_current_image()
                self.update_ui_state()
        except ValueError:
            pass

    def update_ui_state(self):
        # Update navigation buttons
        self.prev_btn.setEnabled(self.current_image_index > 0)
        self.next_btn.setEnabled(self.current_image_index < len(self.images) - 1)
        
        # Update save button
        self.save_annotation_btn.setEnabled(len(self.images) > 0)
        
        # Update jump spinner
        self.jump_spin.setEnabled(len(self.images) > 0)
        self.jump_btn.setEnabled(len(self.images) > 0)
        
        # Update image counter
        if self.images:
            self.image_counter_label.setText(f"Image {self.current_image_index + 1} of {len(self.images)}")
        else:
            self.image_counter_label.setText("No images loaded")

def main():
    app = QApplication(sys.argv)
    window = DesignAnnotationApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()