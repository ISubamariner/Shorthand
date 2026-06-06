export function CreditsPage() {
  return (
    <div className="credits-page">
      <section className="credits-hero">
        <h1>Credits & Attribution</h1>
        <p className="credits-subtitle">
          Teeline ML is built on the shoulders of open-source projects,
          community resources, and freely shared knowledge about the Teeline
          shorthand system.
        </p>
      </section>

      <section className="credits-section">
        <h2>Teeline Symbol Data</h2>
        <div className="credits-card credits-card--featured">
          <h3>
            <a
              href="https://github.com/gonzo-engineering/teeline-online"
              target="_blank"
              rel="noopener noreferrer"
            >
              teeline.online
            </a>
          </h3>
          <span className="credits-license">MIT License</span>
          <p>
            Copyright &copy; 2022{" "}
            <a
              href="https://github.com/gonzo-engineering"
              target="_blank"
              rel="noopener noreferrer"
            >
              Gonzo Engineering
            </a>
          </p>
          <p>
            The hand-drawn Teeline alphabet SVGs that power this application —
            used for both the symbol reference display and as the basis for all
            ML training data — originate from the teeline.online project. The
            outlines were drawn on a tablet in{" "}
            <a
              href="https://krita.org"
              target="_blank"
              rel="noopener noreferrer"
            >
              Krita
            </a>{" "}
            and saved as SVGs.
          </p>
          <p className="credits-usage">
            <strong>Used for:</strong> Symbol reference images, synthetic
            training data generation (2,600+ augmented variants per letter)
          </p>
        </div>
      </section>

      <section className="credits-section">
        <h2>Teeline Shorthand References</h2>
        <p className="credits-intro">
          The Teeline decomposition algorithm — which breaks English words into
          their shorthand letter components — is based on standard Teeline rules
          documented across these community resources:
        </p>
        <ul className="credits-list">
          <li>
            <a
              href="https://en.wikipedia.org/wiki/Teeline_Shorthand"
              target="_blank"
              rel="noopener noreferrer"
            >
              Teeline Shorthand
            </a>{" "}
            — Wikipedia overview of the system and its rules
          </li>
          <li>
            <a
              href="https://github.com/adxsoft/TeelineMate"
              target="_blank"
              rel="noopener noreferrer"
            >
              Teeline Mate
            </a>{" "}
            by @adxsoft — reference implementation of Teeline lookups
          </li>
          <li>
            <a
              href="http://realerthinks.com/a-searchable-teeline-dictionary/"
              target="_blank"
              rel="noopener noreferrer"
            >
              A Searchable Teeline Dictionary
            </a>{" "}
            by Addie Kingsland
          </li>
          <li>
            <a
              href="http://realerthinks.com/teeline-for-the-curious-a-story-of-learning-things-because-i-can/"
              target="_blank"
              rel="noopener noreferrer"
            >
              Teeline for the curious
            </a>{" "}
            by Addie Kingsland — community guide and learning resource
          </li>
          <li>
            <a
              href="https://doi.org/10.35940/ijitee.D1569.029420"
              target="_blank"
              rel="noopener noreferrer"
            >
              Analysis of Teeline Shorthand Recognition using Machine Learning
              and Deep Learning Techniques
            </a>{" "}
            by Mr. Shivaprakash, Dr. Vishwanath C. Burkpalli, Dr. B. S. Anami —{" "}
            <em>
              International Journal of Innovative Technology and Exploring
              Engineering
            </em>
            , Vol. 9, Issue 4, pp. 2133–2138 (2020). Reference for ML approach
            and decomposition rule development.
          </li>
          <li>
            <a
              href="https://css-tricks.com/how-to-get-handwriting-animation-with-irregular-svg-strokes/"
              target="_blank"
              rel="noopener noreferrer"
            >
              How to Get Handwriting Animation With Irregular SVG Strokes
            </a>{" "}
            by Trapti Rahangdale — technique reference via CSS-Tricks
          </li>
        </ul>
      </section>

      <section className="credits-section">
        <h2>Machine Learning</h2>
        <div className="credits-card">
          <h3>Model Architecture</h3>
          <p>
            The recognition model is a custom convolutional neural network (CNN)
            trained from scratch on synthetic data — no pre-trained weights or
            transfer learning. Architecture: 3 convolutional blocks (32 → 64 →
            128 filters) with batch normalization, followed by a dense
            classifier for 26 letter classes.
          </p>
        </div>
        <div className="credits-card">
          <h3>Training Data</h3>
          <p>
            All training data is synthetically generated from the teeline.online
            SVGs using random augmentation (rotation, scale, position shift,
            stroke width variation, noise injection). No handwriting samples from
            real users were used in training.
          </p>
        </div>
        <div className="credits-deps">
          <h3>ML Frameworks</h3>
          <ul>
            <li>
              <a
                href="https://www.tensorflow.org/"
                target="_blank"
                rel="noopener noreferrer"
              >
                TensorFlow
              </a>{" "}
              / Keras — model training{" "}
              <span className="credits-license-inline">Apache 2.0</span>
            </li>
            <li>
              <a
                href="https://www.tensorflow.org/lite"
                target="_blank"
                rel="noopener noreferrer"
              >
                TensorFlow Lite
              </a>{" "}
              — optimized inference runtime{" "}
              <span className="credits-license-inline">Apache 2.0</span>
            </li>
            <li>
              <a
                href="https://numpy.org/"
                target="_blank"
                rel="noopener noreferrer"
              >
                NumPy
              </a>{" "}
              — numerical computation{" "}
              <span className="credits-license-inline">BSD</span>
            </li>
            <li>
              <a
                href="https://scikit-learn.org/"
                target="_blank"
                rel="noopener noreferrer"
              >
                scikit-learn
              </a>{" "}
              — data splitting and evaluation{" "}
              <span className="credits-license-inline">BSD</span>
            </li>
            <li>
              <a
                href="https://pillow.readthedocs.io/"
                target="_blank"
                rel="noopener noreferrer"
              >
                Pillow
              </a>{" "}
              — image processing{" "}
              <span className="credits-license-inline">HPND</span>
            </li>
          </ul>
        </div>
      </section>

      <section className="credits-section">
        <h2>Typography</h2>
        <div className="credits-deps">
          <p className="credits-intro">
            Fonts served via{" "}
            <a
              href="https://fonts.google.com/"
              target="_blank"
              rel="noopener noreferrer"
            >
              Google Fonts
            </a>
            , both under the{" "}
            <a
              href="https://scripts.sil.org/cms/scripts/page.php?site_id=nrsi&id=OFL"
              target="_blank"
              rel="noopener noreferrer"
            >
              SIL Open Font License
            </a>
            .
          </p>
          <ul>
            <li>
              <a
                href="https://fonts.google.com/specimen/Syne"
                target="_blank"
                rel="noopener noreferrer"
              >
                Syne
              </a>{" "}
              — headings and display text. Designed by Lucas Descroix (Bonjour
              Monde)
            </li>
            <li>
              <a
                href="https://fonts.google.com/specimen/DM+Mono"
                target="_blank"
                rel="noopener noreferrer"
              >
                DM Mono
              </a>{" "}
              — body text and monospace. Designed by Colophon Foundry for Google
            </li>
          </ul>
        </div>
      </section>

      <section className="credits-section">
        <h2>Backend</h2>
        <div className="credits-deps">
          <ul>
            <li>
              <a
                href="https://www.djangoproject.com/"
                target="_blank"
                rel="noopener noreferrer"
              >
                Django 5.1
              </a>{" "}
              — web framework{" "}
              <span className="credits-license-inline">BSD</span>
            </li>
            <li>
              <a
                href="https://www.django-rest-framework.org/"
                target="_blank"
                rel="noopener noreferrer"
              >
                Django REST Framework
              </a>{" "}
              — API toolkit{" "}
              <span className="credits-license-inline">BSD</span>
            </li>
            <li>
              <a
                href="https://django-rest-framework-simplejwt.readthedocs.io/"
                target="_blank"
                rel="noopener noreferrer"
              >
                SimpleJWT
              </a>{" "}
              — JWT authentication{" "}
              <span className="credits-license-inline">MIT</span>
            </li>
            <li>
              <a
                href="https://github.com/adamchainz/django-cors-headers"
                target="_blank"
                rel="noopener noreferrer"
              >
                django-cors-headers
              </a>{" "}
              — CORS middleware{" "}
              <span className="credits-license-inline">MIT</span>
            </li>
            <li>
              <a
                href="https://www.psycopg.org/"
                target="_blank"
                rel="noopener noreferrer"
              >
                psycopg2
              </a>{" "}
              — PostgreSQL adapter{" "}
              <span className="credits-license-inline">LGPL</span>
            </li>
            <li>
              <a
                href="https://gunicorn.org/"
                target="_blank"
                rel="noopener noreferrer"
              >
                Gunicorn
              </a>{" "}
              — WSGI HTTP server{" "}
              <span className="credits-license-inline">MIT</span>
            </li>
            <li>
              <a
                href="https://whitenoise.readthedocs.io/"
                target="_blank"
                rel="noopener noreferrer"
              >
                WhiteNoise
              </a>{" "}
              — static file serving{" "}
              <span className="credits-license-inline">MIT</span>
            </li>
            <li>
              <a
                href="https://github.com/jazzband/dj-database-url"
                target="_blank"
                rel="noopener noreferrer"
              >
                dj-database-url
              </a>{" "}
              — database URL configuration{" "}
              <span className="credits-license-inline">BSD</span>
            </li>
          </ul>
        </div>
      </section>

      <section className="credits-section">
        <h2>Frontend</h2>
        <div className="credits-deps">
          <ul>
            <li>
              <a
                href="https://react.dev/"
                target="_blank"
                rel="noopener noreferrer"
              >
                React 18
              </a>{" "}
              — UI library{" "}
              <span className="credits-license-inline">MIT</span>
            </li>
            <li>
              <a
                href="https://reactrouter.com/"
                target="_blank"
                rel="noopener noreferrer"
              >
                React Router 6
              </a>{" "}
              — client-side routing{" "}
              <span className="credits-license-inline">MIT</span>
            </li>
            <li>
              <a
                href="https://www.typescriptlang.org/"
                target="_blank"
                rel="noopener noreferrer"
              >
                TypeScript
              </a>{" "}
              — type-safe JavaScript{" "}
              <span className="credits-license-inline">Apache 2.0</span>
            </li>
            <li>
              <a
                href="https://vite.dev/"
                target="_blank"
                rel="noopener noreferrer"
              >
                Vite
              </a>{" "}
              — build tool and dev server{" "}
              <span className="credits-license-inline">MIT</span>
            </li>
          </ul>
        </div>
      </section>

      <section className="credits-section">
        <h2>Infrastructure</h2>
        <div className="credits-deps">
          <ul>
            <li>
              <a
                href="https://www.postgresql.org/"
                target="_blank"
                rel="noopener noreferrer"
              >
                PostgreSQL 15
              </a>{" "}
              — database{" "}
              <span className="credits-license-inline">PostgreSQL License</span>
            </li>
            <li>
              <a
                href="https://www.docker.com/"
                target="_blank"
                rel="noopener noreferrer"
              >
                Docker
              </a>{" "}
              — containerization{" "}
              <span className="credits-license-inline">Apache 2.0</span>
            </li>
            <li>
              <a
                href="https://render.com/"
                target="_blank"
                rel="noopener noreferrer"
              >
                Render
              </a>{" "}
              — backend hosting
            </li>
            <li>
              <a
                href="https://vercel.com/"
                target="_blank"
                rel="noopener noreferrer"
              >
                Vercel
              </a>{" "}
              — frontend hosting
            </li>
          </ul>
        </div>
      </section>

      <section className="credits-section">
        <h2>Docker Base Images</h2>
        <div className="credits-deps">
          <ul>
            <li>
              <code>python:3.11-slim</code> — official Python image{" "}
              <span className="credits-license-inline">PSF License</span>
            </li>
            <li>
              <code>node:20-alpine</code> — official Node.js image{" "}
              <span className="credits-license-inline">MIT</span>
            </li>
            <li>
              <code>postgres:15-alpine</code> — official PostgreSQL image{" "}
              <span className="credits-license-inline">PostgreSQL License</span>
            </li>
          </ul>
        </div>
      </section>

      <section className="credits-section credits-footer">
        <h2>License</h2>
        <p>
          Teeline ML Checker is open source under the{" "}
          <a
            href="https://opensource.org/licenses/MIT"
            target="_blank"
            rel="noopener noreferrer"
          >
            MIT License
          </a>
          . Copyright &copy; 2026 Ian Salig Batangan.
        </p>
        <p className="credits-note">
          Teeline shorthand was created by James Hill in 1968 and is widely
          taught in journalism programs, particularly in the UK. This project is
          an independent learning tool and is not affiliated with any official
          Teeline organization.
        </p>
      </section>
    </div>
  );
}
