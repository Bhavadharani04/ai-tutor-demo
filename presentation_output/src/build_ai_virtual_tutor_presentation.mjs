import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, "..", "..");
const OUTPUT_DIR = path.join(ROOT, "presentation_output");
const PREVIEW_DIR = path.join(OUTPUT_DIR, "previews_40");
const PPTX_PATH = path.join(OUTPUT_DIR, "AI_Virtual_Tutor_40_Slides.pptx");
const LAYOUT_PATH = path.join(OUTPUT_DIR, "AI_Virtual_Tutor_40_Slides.layout.json");
const SKIA_CANVAS_PATH = pathToFileURL(
  path.join(
    "C:\\Users\\Bavadharani\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\node\\node_modules\\@oai\\artifact-tool\\node_modules\\skia-canvas\\lib\\index.mjs",
  ),
).href;
const ARTIFACT_TOOL_PATH = pathToFileURL(
  path.join(
    "C:\\Users\\Bavadharani\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\node\\node_modules\\@oai\\artifact-tool\\dist\\artifact_tool.mjs",
  ),
).href;

const COLORS = {
  ink: "#16233B",
  muted: "#53627A",
  accent: "#D66B3D",
  accentSoft: "#F0C8B5",
  line: "#C9D3E1",
  deep: "#1E315C",
  paper: "#F7F3EC",
  gold: "#BE8A39",
};

const {
  Presentation,
  PresentationFile,
  row,
  column,
  text,
  rule,
  fill,
  fixed,
  hug,
  wrap,
  createPresentationLayoutExportBlob,
  drawSlideToCtx,
} = await import(ARTIFACT_TOOL_PATH);

const slides = [
  {
    kind: "cover",
    title: "AI Virtual Tutor",
    subtitle:
      "A 40-slide project presentation covering the introduction, objectives, applications, methodology, module design, expected output, and system requirements of the proposed intelligent tutoring platform.",
    note: "Project presentation for academic review and viva support",
  },
  {
    kind: "content",
    section: "Project Opening",
    title: "Project Overview",
    body:
      "AI Virtual Tutor is an educational web application designed to answer student doubts in a natural, supportive, and interactive way. The project combines conversational AI, voice support, file understanding, chat memory, and visual explanation features inside one learning interface. Instead of behaving like a search box, the system behaves like a patient teacher who explains concepts step by step, remembers the context of the conversation, and keeps the learner engaged throughout the session.",
    takeaway: "Core idea: turn AI assistance into a guided learning experience instead of one-time question answering.",
  },
  {
    kind: "section",
    sectionNumber: "01",
    sectionTitle: "Introduction",
    statement:
      "This section explains why the project is needed, what educational gap it addresses, and how the idea of an AI tutor becomes a practical software solution.",
  },
  {
    kind: "content",
    section: "Introduction",
    title: "Background of the Topic",
    body:
      "Students often need immediate clarification while studying technical subjects, especially in fields like artificial intelligence, machine learning, and data science. Traditional learning support depends heavily on classroom time, availability of faculty, or static materials such as notes and videos. These options are useful, but they do not always provide instant personalized answers. The project emerges from this gap by using modern AI to simulate a responsive tutor that can explain, repeat, and adapt information on demand.",
    takeaway: "The background is rooted in the growing demand for continuous, personalized digital learning support.",
  },
  {
    kind: "content",
    section: "Introduction",
    title: "Need for an AI Tutor",
    body:
      "A learner may understand one concept today and struggle with a connected idea tomorrow, so support has to be available beyond classroom hours. An AI tutor is valuable because it reduces waiting time, encourages students to ask questions without hesitation, and provides a conversational environment where learning can continue at the learner's pace. By supporting text, voice, and document-based interaction, the system becomes more inclusive and practical for different learning styles.",
    takeaway: "The need is not only for automation, but for access, confidence, and continuity in learning.",
  },
  {
    kind: "content",
    section: "Introduction",
    title: "Problem Statement",
    body:
      "Many students struggle to obtain quick, concept-oriented explanations when they are learning independently. Existing tools may produce generic answers, fail to retain conversational context, or lack features like voice guidance, file understanding, and topic-focused history. Because of these limitations, students often move between multiple apps for reading, asking, revising, and clarifying. The problem addressed in this project is how to build a unified tutoring system that feels interactive, remembers context, and explains AI-related topics clearly.",
    takeaway: "The problem is fragmentation of learning support and lack of personalized real-time doubt resolution.",
  },
  {
    kind: "content",
    section: "Introduction",
    title: "Project Definition",
    body:
      "AI Virtual Tutor is defined as an intelligent educational assistant that accepts user input through text, voice, or files and returns understandable topic explanations in a teacher-like tone. It is not intended to replace teachers, but to act as a supportive layer between study sessions, assignments, and revision work. The system is designed specifically around AI topics so that its knowledge boundaries stay meaningful and its responses remain relevant to the academic context for which it is built.",
    takeaway: "The project is a focused tutoring assistant, not a general-purpose chatbot for every topic.",
  },
  {
    kind: "content",
    section: "Introduction",
    title: "Aim of the Project",
    body:
      "The main aim of the project is to create an AI-powered learning assistant that can simplify complex artificial intelligence concepts and deliver them in a student-friendly way. The application seeks to reduce confusion, improve concept retention, and make technical learning more approachable by combining conversational explanations, visual outputs, and memory of previous sessions. In simple terms, the goal is to make digital doubt-solving feel more like guided teaching and less like isolated information retrieval.",
    takeaway: "The aim is meaningful teaching support through approachable, context-aware AI interaction.",
  },
  {
    kind: "section",
    sectionNumber: "02",
    sectionTitle: "Objectives and Scope",
    statement:
      "This section translates the project vision into concrete objectives, feature goals, and the boundaries within which the proposed system is designed to operate.",
  },
  {
    kind: "content",
    section: "Objectives",
    title: "Primary Objective",
    body:
      "The primary objective is to provide real-time, understandable, and topic-focused explanations for AI concepts through an interactive software interface. The tutor should handle student questions in plain language, preserve the flow of discussion across a session, and present responses in a manner that is informative without being intimidating. This objective drives the choice of conversational AI, user-friendly frontend design, and session-based storage used throughout the project.",
    takeaway: "The first objective is clear concept explanation delivered immediately and conversationally.",
  },
  {
    kind: "content",
    section: "Objectives",
    title: "Functional Objectives",
    body:
      "The system is expected to support several practical goals: accepting text questions, recognizing voice input, reading uploaded files such as PDFs and images, storing chat history, and generating responses that stay within the intended AI-learning domain. Beyond this, the application also aims to generate architecture diagrams and topic visuals so that explanation is not limited to text alone. Each functional objective contributes to the idea of a complete tutoring workspace rather than a minimal chat tool.",
    takeaway: "Functional objectives focus on multimodal interaction, memory, and richer explanation formats.",
  },
  {
    kind: "content",
    section: "Objectives",
    title: "Scope of the Project",
    body:
      "The current scope of the project is intentionally focused on artificial intelligence, machine learning, deep learning, and related technical topics. This focused scope improves response quality because the tutor can be tuned for a narrower academic domain instead of attempting to answer every possible question. The project includes a web-based user interface, a Python Flask backend, session storage through SQLite, and optional diagram and image support to enrich explanations.",
    takeaway: "A well-defined scope improves relevance, maintainability, and academic clarity.",
  },
  {
    kind: "section",
    sectionNumber: "03",
    sectionTitle: "Applications",
    statement:
      "This section shows where the AI Virtual Tutor can be used in practical learning environments and how its features support different kinds of students and study tasks.",
  },
  {
    kind: "content",
    section: "Applications",
    title: "General Educational Application",
    body:
      "The most direct application of the project is as a digital assistant for students learning AI concepts through classroom courses, online videos, or self-study. Whenever the learner encounters confusion about a term, workflow, or model, the tutor can provide an immediate explanation inside the same interface. This reduces interruptions in the learning process and helps the student maintain momentum rather than pausing study to search across multiple websites or notes.",
    takeaway: "The system is best understood as an always-available academic companion for concept clarification.",
  },
  {
    kind: "content",
    section: "Applications",
    title: "Self-Learning and Revision",
    body:
      "Students preparing for exams or learning on their own often need short explanations, repeated examples, and topic recall support. The tutor is useful in this context because it can respond instantly, retain session context, and help revisit earlier subjects through chat history. A revision-oriented workflow becomes easier when the learner can ask, compare, and summarize concepts continuously without rebuilding context from the beginning each time.",
    takeaway: "Revision becomes more effective when conversation history and contextual follow-up are available.",
  },
  {
    kind: "content",
    section: "Applications",
    title: "Document-Based Learning",
    body:
      "Many students learn from PDFs, screenshots, and notes rather than from direct question-answer sessions. Because this project accepts supported file uploads, it can analyze learning material and respond based on the content of the file. This is useful when the learner wants a quick explanation of a diagram, page, or extracted note without copying everything manually. It makes the tutor relevant not only for conversation, but also for study material interpretation.",
    takeaway: "File-based interaction extends the tutor from chat support to study-material assistance.",
  },
  {
    kind: "content",
    section: "Applications",
    title: "Voice-Enabled Learning",
    body:
      "Voice interaction broadens accessibility and convenience by allowing students to speak questions instead of typing them. This application is especially useful for learners who prefer auditory interaction, are revising while multitasking, or simply want a more natural tutoring experience. When combined with spoken responses, the system begins to feel more like a verbal teaching exchange, which can make learning less mechanical and more engaging for many users.",
    takeaway: "Voice support improves accessibility, comfort, and the human feel of the tutoring experience.",
  },
  {
    kind: "section",
    sectionNumber: "04",
    sectionTitle: "Proposed Methodology",
    statement:
      "This section explains how the project is designed, how data moves through the system, and how each technical step supports the educational objectives of the tutor.",
  },
  {
    kind: "content",
    section: "Methodology",
    title: "Methodology Overview",
    body:
      "The proposed methodology follows a layered approach in which the user interface, conversational logic, domain filtering, content enhancement, and session storage work together as one pipeline. The student begins from a simple web interface, submits a query by text, voice, or file, and the system classifies the request before routing it to the appropriate response path. This method keeps the user experience simple while allowing the backend to support multiple intelligent behaviors under the surface.",
    takeaway: "The methodology is pipeline-driven, with user simplicity on the outside and structured intelligence inside.",
  },
  {
    kind: "content",
    section: "Methodology",
    title: "Knowledge and Prompt Design Stage",
    body:
      "The second stage focuses on how the tutor should think and speak. Domain-specific knowledge notes, example guidance, follow-up handling, and prompt rules are used so that the AI responds like a patient tutor instead of a generic assistant. The methodology also includes out-of-scope detection to keep the system inside its academic purpose. This stage is essential because educational quality depends not only on model power, but also on how the model is guided.",
    takeaway: "Good tutoring behavior is shaped by prompt design, topic boundaries, and response guidance.",
  },
  {
    kind: "content",
    section: "Methodology",
    title: "Backend Processing Stage",
    body:
      "The backend stage is responsible for receiving requests, classifying them, calling the correct services, and packaging responses for the frontend. Flask is used as the main framework because it is lightweight, easy to organize, and suitable for API-based communication with the client side. Within this stage, the application distinguishes between normal explanatory responses, diagram requests, and image generation requests so that each path can apply its own logic while still belonging to one tutoring system.",
    takeaway: "Backend design turns one chat interface into multiple specialized response workflows.",
  },
  {
    kind: "content",
    section: "Methodology",
    title: "Frontend Interaction Stage",
    body:
      "The frontend stage translates technical functionality into a student-friendly experience. It provides login, chat history, file upload, voice controls, topic progress tracking, and response rendering in a single page. This methodology choice is important because even a powerful AI backend becomes difficult to use if the interface feels fragmented or confusing. The frontend therefore acts as the learning surface where clarity, comfort, and continuity directly influence user satisfaction.",
    takeaway: "The interface is treated as part of the learning methodology, not just as a display layer.",
  },
  {
    kind: "content",
    section: "Methodology",
    title: "Session and Memory Stage",
    body:
      "To support follow-up questions and meaningful continuity, the project includes a session-management stage that stores messages in a SQLite database. Each conversation receives a session identity and can later be reopened from the history panel. This methodology improves tutoring quality because many learning questions depend on the context of what was asked before. Without memory, every question becomes isolated; with memory, the tutor can continue explanations naturally.",
    takeaway: "Persistent session memory converts the system from isolated Q&A into connected tutoring dialogue.",
  },
  {
    kind: "content",
    section: "Methodology",
    title: "Testing and Refinement Stage",
    body:
      "The final stage of the methodology is iterative testing and refinement. During development, the system is checked for response flow, session storage, visual rendering, topic filtering, and overall usability. Runtime outputs such as generated images and stored histories help verify whether the tutor behaves as expected across realistic learning scenarios. This stage ensures that the project is not merely coded, but evaluated as a working academic application with visible learner-facing behavior.",
    takeaway: "Testing focuses on practical tutoring behavior, not only on backend correctness.",
  },
  {
    kind: "section",
    sectionNumber: "05",
    sectionTitle: "Module Description",
    statement:
      "This section breaks the project into functional modules so the design can be explained clearly, implemented systematically, and justified during technical review.",
  },
  {
    kind: "content",
    section: "Modules",
    title: "Overall Module View",
    body:
      "The project is organized into independent but connected modules so that each responsibility remains clear. At a high level, the system includes a user access module, chat interaction module, voice module, file processing module, AI response module, visual generation module, and database/history module. This modular structure makes the application easier to maintain, test, and enhance because changes in one area can often be handled without rewriting the entire project.",
    takeaway: "Module-based design supports clarity, maintenance, and future scalability.",
  },
  {
    kind: "content",
    section: "Modules",
    title: "Login and User Session Module",
    body:
      "The login and session module manages initial user entry into the application and stores the learner's name for personalized interaction. Although the current access control is lightweight, it still plays an important academic role by making the system feel individual and by supporting continuity across visits. Once the user enters the application, the module helps establish the initial learning context, displays a personalized greeting, and connects the student identity with later session activity.",
    takeaway: "This module personalizes the experience and prepares the system for session-based tutoring.",
  },
  {
    kind: "content",
    section: "Modules",
    title: "Chat Interaction Module",
    body:
      "The chat interaction module is the main user communication layer of the project. It captures typed questions, shows user and assistant bubbles, triggers request submission, and renders the returned explanations in a readable way. Because the project depends heavily on conversation flow, this module is central to usability. It also handles loading old conversations, updating titles, and keeping the tutoring exchange visible as an organized, scrollable learning history.",
    takeaway: "The chat module is the heart of day-to-day user interaction with the tutor.",
  },
  {
    kind: "content",
    section: "Modules",
    title: "Voice Input and Output Module",
    body:
      "The voice module allows the user to ask questions through speech and listen to the tutor's reply through browser speech features. This module is valuable because it supports natural communication and helps users who may prefer hearing explanations rather than reading long responses. From a system perspective, it enriches the interface without changing the core tutoring logic, which means voice becomes another route into the same educational pipeline already used by typed messages.",
    takeaway: "Voice support increases accessibility while reusing the same tutoring intelligence underneath.",
  },
  {
    kind: "content",
    section: "Modules",
    title: "Document and File Processing Module",
    body:
      "The file processing module accepts supported uploads such as PDFs and images and converts them into meaningful input for the tutor. PDF text can be extracted for explanation, while images can be interpreted in relation to AI or technical ideas. This module expands the value of the project beyond direct questions because students often study from notes, diagrams, and screenshots. Instead of forcing manual rewriting, the module lets the learner bring study material directly into the tutoring flow.",
    takeaway: "This module bridges the gap between learning resources and conversational explanation.",
  },
  {
    kind: "content",
    section: "Modules",
    title: "AI Response Generation Module",
    body:
      "The AI response generation module is responsible for analyzing the user query, retrieving relevant context, and producing the final tutor-style explanation. It includes topic relevance checks, greeting handling, follow-up support, system prompting, and controlled domain behavior. This module is where the academic identity of the project becomes strongest, because the model is instructed not only to answer, but to teach in a step-by-step and encouraging way suited to student understanding.",
    takeaway: "This module defines the educational quality and personality of the tutor.",
  },
  {
    kind: "content",
    section: "Modules",
    title: "Diagram and Image Generation Module",
    body:
      "The visual generation module handles special requests that benefit from structured or illustrated output. It can create architecture-style diagrams for AI topics and generate educational visuals that are stored and shown inside the same chat interface. This module makes the project stand out from basic tutoring apps because it supports visual learning directly inside the tutoring conversation. It also demonstrates how AI services can be combined to improve conceptual understanding.",
    takeaway: "Visual generation transforms explanation from text-only teaching into multimodal learning support.",
  },
  {
    kind: "content",
    section: "Modules",
    title: "Database and History Module",
    body:
      "The database and history module stores sessions and messages using SQLite so that the learner can reopen previous conversations whenever needed. This module is useful for revision, continued learning, and long-term tracking of discussed topics. It also supports interface features such as chat history sidebars, automatic session naming, and topic persistence. In academic terms, it gives the application memory, which is one of the key qualities that turns a chatbot interaction into an ongoing tutoring relationship.",
    takeaway: "Stored history gives the project educational continuity and revision value.",
  },
  {
    kind: "section",
    sectionNumber: "06",
    sectionTitle: "Expected Output and Requirements",
    statement:
      "This final technical section explains what the completed system is expected to deliver and what hardware, software, and runtime conditions are needed for successful operation.",
  },
  {
    kind: "content",
    section: "Outputs",
    title: "Expected Output of the System",
    body:
      "The expected output is a working AI tutoring application that allows a student to log in, ask topic-specific questions, upload learning material, receive clear teaching-style answers, and revisit saved conversations later. In addition to textual explanations, the system should be able to provide diagrams and educational images for selected topics. The final output is therefore not just code, but a complete interactive learning environment demonstrating real-time doubt resolution and supportive AI communication.",
    takeaway: "The expected output is a functional tutoring product, not merely a proof-of-concept backend.",
  },
  {
    kind: "content",
    section: "Outputs",
    title: "User-Facing Output",
    body:
      "From the learner's perspective, the output appears as a polished chat-based study system with topic explanations, voice assistance, visual responses, history tracking, and a guided conversational tone. The interface should help the student feel oriented and supported rather than overwhelmed. A successful user-facing output is one where the learner can move naturally from asking a doubt to receiving a clear answer, continuing the discussion, and reviewing the same topic again later through saved session history.",
    takeaway: "Good output is measured by usability and clarity as much as by technical correctness.",
  },
  {
    kind: "content",
    section: "Outputs",
    title: "System Requirements",
    body:
      "The project requires a development environment capable of running Python, Flask, and the necessary AI-related dependencies. At the software level, it depends on configured API access for the selected language model and image features, environment variables for secure runtime setup, and browser support for the frontend speech capabilities. At the system level, a standard modern computer with internet connectivity, a supported browser, and enough storage for generated assets and the SQLite database is sufficient for operation.",
    takeaway: "Requirements are moderate, which makes the project practical for student-level deployment and demo use.",
  },
  {
    kind: "content",
    section: "Outputs",
    title: "Hardware and Runtime Requirements",
    body:
      "The hardware requirement is comparatively light because most of the intelligence is provided through external model services rather than heavy local training. A standard laptop or desktop with a modern browser is generally enough to run the tutor, provided internet access is available for API-backed features. Runtime reliability mainly depends on environment configuration, valid API keys, browser compatibility, and sufficient local permission for storing generated images and database records.",
    takeaway: "The project is accessible to typical student hardware and does not demand specialized machines.",
  },
  {
    kind: "content",
    section: "Outputs",
    title: "Benefits and Future Enhancements",
    body:
      "The project already demonstrates clear benefits in accessibility, response speed, concept clarification, and multimodal tutoring. Future enhancements could include stronger authentication, subject expansion beyond AI, better learner analytics, more adaptive quizzes, multilingual support, and smarter personalization based on previous performance. These improvements would not change the central idea of the project; instead, they would deepen the same goal of making intelligent tutoring more supportive, scalable, and educationally effective.",
    takeaway: "The present system is useful on its own, while future upgrades can increase reach and personalization.",
  },
  {
    kind: "content",
    section: "Conclusion",
    title: "Conclusion",
    body:
      "AI Virtual Tutor is a focused academic project that combines conversational AI, web development, session storage, voice interaction, and visual explanation into one educational platform. It addresses a real student problem by providing on-demand, understandable support for AI-related learning topics. The project is technically meaningful because it integrates multiple modules into a cohesive product, and academically meaningful because it places clarity, confidence, and continuity at the center of digital learning assistance.",
    takeaway: "The project succeeds when technology and teaching quality work together as one system.",
  },
];

function titleStyle(size, color = COLORS.ink) {
  return {
    fontSize: size,
    bold: true,
    color,
  };
}

function bodyStyle(size = 28, color = COLORS.ink) {
  return {
    fontSize: size,
    color,
  };
}

function addCoverSlide(presentation, slideData) {
  const slide = presentation.slides.add();
  slide.compose(
    row(
      {
        name: "cover-root",
        width: fill,
        height: fill,
        padding: { x: 88, y: 74 },
        gap: 72,
      },
      [
        column(
          {
            name: "cover-left",
            width: wrap(980),
            height: fill,
            gap: 26,
          },
          [
            text("PROJECT PRESENTATION", {
              name: "cover-kicker",
              width: wrap(420),
              height: hug,
              style: bodyStyle(20, COLORS.accent),
            }),
            text(slideData.title, {
              name: "cover-title",
              width: wrap(900),
              height: hug,
              style: titleStyle(66, COLORS.deep),
            }),
            rule({
              name: "cover-rule",
              width: fixed(260),
              stroke: COLORS.accent,
              weight: 5,
            }),
            text(slideData.subtitle, {
              name: "cover-subtitle",
              width: wrap(900),
              height: hug,
              style: bodyStyle(28, COLORS.muted),
            }),
            text(slideData.note, {
              name: "cover-note",
              width: wrap(700),
              height: hug,
              style: bodyStyle(18, COLORS.gold),
            }),
          ],
        ),
        column(
          {
            name: "cover-right",
            width: wrap(520),
            height: fill,
            gap: 22,
          },
          [
            text("Project review format", {
              name: "cover-topic-1",
              width: wrap(520),
              height: hug,
              style: titleStyle(28, COLORS.gold),
            }),
            text(
              "Introduction, objectives, applications, methodology, module description, expected output, and system requirements are arranged in a clean academic sequence for presentation and viva use.",
              {
                name: "cover-topic-2",
                width: wrap(520),
                height: hug,
                style: bodyStyle(23, COLORS.muted),
              },
            ),
            text("40 slides | paragraph format | project-focused narrative", {
              name: "cover-topic-3",
              width: wrap(520),
              height: hug,
              style: bodyStyle(20, COLORS.accent),
            }),
          ],
        ),
      ],
    ),
    {
      frame: { left: 0, top: 0, width: 1920, height: 1080 },
      baseUnit: 8,
    },
  );
}

function addSectionSlide(presentation, slideData, slideIndex) {
  const slide = presentation.slides.add();
  slide.compose(
    column(
      {
        name: `section-root-${slideIndex}`,
        width: fill,
        height: fill,
        padding: { x: 110, y: 110 },
        gap: 26,
      },
      [
        text(slideData.sectionNumber, {
          name: `section-number-${slideIndex}`,
          width: wrap(300),
          height: hug,
          style: titleStyle(110, COLORS.accentSoft),
        }),
        text(slideData.sectionTitle, {
          name: `section-title-${slideIndex}`,
          width: wrap(1200),
          height: hug,
          style: titleStyle(62, COLORS.deep),
        }),
        rule({
          name: `section-rule-${slideIndex}`,
          width: fixed(320),
          stroke: COLORS.accent,
          weight: 5,
        }),
        text(slideData.statement, {
          name: `section-statement-${slideIndex}`,
          width: wrap(1300),
          height: hug,
          style: bodyStyle(30, COLORS.muted),
        }),
        text(`Slide ${slideIndex + 1} of ${slides.length}`, {
          name: `section-page-${slideIndex}`,
          width: wrap(240),
          height: hug,
          style: bodyStyle(18, COLORS.gold),
        }),
      ],
    ),
    {
      frame: { left: 0, top: 0, width: 1920, height: 1080 },
      baseUnit: 8,
    },
  );
}

function addContentSlide(presentation, slideData, slideIndex) {
  const slide = presentation.slides.add();
  const accentColor = slideIndex % 2 === 0 ? COLORS.accent : COLORS.gold;
  slide.compose(
    row(
      {
        name: `content-root-${slideIndex}`,
        width: fill,
        height: fill,
        padding: { x: 84, y: 72 },
        gap: 54,
      },
      [
        column(
          {
            name: `content-meta-${slideIndex}`,
            width: fixed(240),
            height: fill,
            gap: 18,
          },
          [
            text(String(slideIndex + 1).padStart(2, "0"), {
              name: `content-number-${slideIndex}`,
              width: wrap(220),
              height: hug,
              style: titleStyle(78, accentColor),
            }),
            text(slideData.section.toUpperCase(), {
              name: `content-section-${slideIndex}`,
              width: wrap(220),
              height: hug,
              style: bodyStyle(18, COLORS.muted),
            }),
            rule({
              name: `content-rule-${slideIndex}`,
              width: fixed(180),
              stroke: accentColor,
              weight: 4,
            }),
          ],
        ),
        column(
          {
            name: `content-main-${slideIndex}`,
            width: wrap(1450),
            height: fill,
            gap: 22,
          },
          [
            text(slideData.title, {
              name: `content-title-${slideIndex}`,
              width: wrap(1380),
              height: hug,
              style: titleStyle(48, COLORS.deep),
            }),
            text(slideData.body, {
              name: `content-body-${slideIndex}`,
              width: wrap(1380),
              height: hug,
              style: bodyStyle(26, COLORS.ink),
            }),
            text(slideData.takeaway, {
              name: `content-takeaway-${slideIndex}`,
              width: wrap(1300),
              height: hug,
              style: bodyStyle(20, accentColor),
            }),
            text(`Slide ${slideIndex + 1} of ${slides.length}`, {
              name: `content-page-${slideIndex}`,
              width: wrap(220),
              height: hug,
              style: bodyStyle(16, COLORS.muted),
            }),
          ],
        ),
      ],
    ),
    {
      frame: { left: 0, top: 0, width: 1920, height: 1080 },
      baseUnit: 8,
    },
  );
}

function buildPresentation() {
  const presentation = Presentation.create({
    slideSize: { width: 1920, height: 1080 },
  });

  slides.forEach((slideData, slideIndex) => {
    if (slideData.kind === "cover") {
      addCoverSlide(presentation, slideData);
      return;
    }
    if (slideData.kind === "section") {
      addSectionSlide(presentation, slideData, slideIndex);
      return;
    }
    addContentSlide(presentation, slideData, slideIndex);
  });

  return presentation;
}

async function exportDeck(presentation) {
  const pptxBlob = await PresentationFile.exportPptx(presentation);
  await pptxBlob.save(PPTX_PATH);
}

async function exportLayout(presentation) {
  try {
    const layoutBlob = await createPresentationLayoutExportBlob(presentation);
    await layoutBlob.save(LAYOUT_PATH);
  } catch (error) {
    console.warn(`Layout export skipped: ${error.message}`);
  }
}

async function exportPreviews(presentation) {
  const { Canvas } = await import(SKIA_CANVAS_PATH);
  const slideList = presentation.slides.items;
  for (let index = 0; index < slideList.length; index += 1) {
    const slide = slideList[index];
    const canvas = new Canvas(1920, 1080);
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = COLORS.paper;
    ctx.fillRect(0, 0, 1920, 1080);
    await drawSlideToCtx(slide, presentation, ctx, undefined, undefined, undefined, undefined, undefined, undefined, undefined, {
      clearBeforeDraw: false,
    });
    const previewPath = path.join(
      PREVIEW_DIR,
      `slide-${String(index + 1).padStart(2, "0")}.png`,
    );
    await canvas.saveAs(previewPath);
  }
}

async function main() {
  await fs.mkdir(OUTPUT_DIR, { recursive: true });
  await fs.mkdir(PREVIEW_DIR, { recursive: true });

  const presentation = buildPresentation();
  await exportDeck(presentation);
  await exportPreviews(presentation);
  await exportLayout(presentation);

  console.log(`Deck exported: ${PPTX_PATH}`);
  console.log(`Layout exported: ${LAYOUT_PATH}`);
  console.log(`Previews exported: ${PREVIEW_DIR}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
