import { Link } from "react-router-dom";

export function AboutPage() {
  return (
    <div className="main about-page">
      <section className="about-hero">
        <p className="eyebrow">Free &amp; Open Source</p>
        <h1 className="section-title">
          Teeline <span className="accent">ML</span>
        </h1>
        <p className="about-tagline">
          Practice Teeline shorthand letter forms and get instant feedback
          powered by machine learning.
        </p>
        <p className="about-pitch">
          Draw any Teeline letter on the canvas, and a trained neural network
          identifies what you wrote in under a second. Track your accuracy per
          symbol, build streaks, practice full words, and see how you rank on
          the leaderboard. No sign-up required to start.
        </p>
        <div className="about-cta">
          <Link to="/" className="btn btn-primary">
            Start Practicing
          </Link>
        </div>
        <p className="about-attribution">Built by Ian</p>
      </section>

      <section className="about-section">
        <p className="eyebrow">What You Can Do</p>
        <h2 className="about-heading">Features</h2>

        <div className="about-features">
          <div className="card about-feature">
            <div className="about-feature-icon">&#9998;</div>
            <h3 className="about-feature-title">Letter Practice</h3>
            <p className="about-feature-desc">
              Draw individual Teeline characters on a guided canvas with
              ascender, x-height, baseline, and descender lines. The ML model
              predicts your letter and tells you instantly whether it's correct.
            </p>
          </div>

          <div className="card about-feature">
            <div className="about-feature-icon">&#9997;</div>
            <h3 className="about-feature-title">Word Practice</h3>
            <p className="about-feature-desc">
              Practice writing full words broken down into their Teeline letter
              components. The app uses a decomposition engine that handles vowel
              dropping, consonant blends, and R-doubling — the core rules of
              Teeline.
            </p>
          </div>

          <div className="card about-feature">
            <div className="about-feature-icon">&#9652;</div>
            <h3 className="about-feature-title">Progress Tracking</h3>
            <p className="about-feature-desc">
              See your accuracy for every letter, identify your weakest symbols,
              and track streaks. The scoring system rewards consistency: base
              points for correct answers, bonuses for streaks and high
              confidence.
            </p>
          </div>

          <div className="card about-feature">
            <div className="about-feature-icon">&#9733;</div>
            <h3 className="about-feature-title">Leaderboard</h3>
            <p className="about-feature-desc">
              Compete with other Teeline learners. Scores are ranked by total
              points earned through practice. Create an account to claim your
              spot and preserve your progress across devices.
            </p>
          </div>
        </div>
      </section>

      <section className="about-section">
        <p className="eyebrow">Under the Hood</p>
        <h2 className="about-heading">How It Works</h2>

        <div className="about-pipeline">
          <div className="about-step">
            <div className="about-step-number">1</div>
            <div className="about-step-content">
              <h3 className="about-step-title">Draw</h3>
              <p className="about-step-desc">
                You draw a Teeline letter on the canvas. The drawing is captured
                as a PNG image and sent to the backend.
              </p>
            </div>
          </div>

          <div className="about-step-connector" />

          <div className="about-step">
            <div className="about-step-number">2</div>
            <div className="about-step-content">
              <h3 className="about-step-title">Predict</h3>
              <p className="about-step-desc">
                A MobileNetV2 neural network, trained on Teeline handwriting
                samples and compressed to TensorFlow Lite for fast inference,
                classifies the image and returns a prediction with a confidence
                score.
              </p>
            </div>
          </div>

          <div className="about-step-connector" />

          <div className="about-step">
            <div className="about-step-number">3</div>
            <div className="about-step-content">
              <h3 className="about-step-title">Feedback</h3>
              <p className="about-step-desc">
                You see the result instantly: correct or incorrect, the
                predicted letter, the model's confidence, and points earned.
                Streaks build with consecutive correct answers.
              </p>
            </div>
          </div>
        </div>

        <div className="card about-tech-note">
          <p className="eyebrow">Teeline Decomposition</p>
          <p className="about-tech-desc">
            For word practice, a custom decomposition engine converts English
            words into Teeline letter sequences by applying phonetic rules:
            vowels are dropped (except at the start), silent letters removed,
            double consonants reduced, and special blends and R-doubling rules
            applied. This means every word in the dictionary can be practiced
            without manual curation.
          </p>
        </div>
      </section>

      <section className="about-section about-footer-note">
        <p className="about-hosting-note">
          This app runs on free-tier hosting, so cold starts may take a few
          seconds. The ML model and all practice data are fully functional.
        </p>
        <div className="about-cta">
          <Link to="/" className="btn btn-primary">
            Start Practicing
          </Link>
        </div>
        <p className="about-hosting-note" style={{ marginTop: 16 }}>
          <Link to="/credits" style={{ color: "var(--accent)" }}>
            Credits &amp; Attribution
          </Link>
        </p>
      </section>
    </div>
  );
}
