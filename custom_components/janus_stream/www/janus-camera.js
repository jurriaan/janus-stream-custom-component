import Janus from "./adapter-and-janus.js";

class JanusCard extends HTMLElement {
  set hass(hass) {
    const entityId = this.config.entity;
    const state = hass.states[entityId];

    if (!this.remoteVideo) {
      const card = document.createElement("ha-card");
      card.style.overflow = "hidden";
      const remoteVideo = document.createElement("video");
      remoteVideo.style.display = "block";
      remoteVideo.style.width = "100%";
      remoteVideo.defaultMuted = true;
      remoteVideo.muted = true;
      remoteVideo.playsInline = true;
      remoteVideo.autoplay = true;
      remoteVideo.controls = true;
      remoteVideo.setAttribute("playsinline", "");
      remoteVideo.setAttribute("autoplay", "");
      remoteVideo.setAttribute("muted", "");
      this.remoteVideo = remoteVideo;

      const observer = new IntersectionObserver(
        (entries, observer) => {
          entries.forEach((entry) => {
            entry.isIntersecting ? remoteVideo.play() : remoteVideo.pause();
          });
        },
        { threshold: this.config.intersection || 0.5 }
      );
      observer.observe(remoteVideo);

      card.appendChild(remoteVideo);
      this.appendChild(card);

      hass.connection
        .sendMessagePromise({
          type: "janus/stream_configuration",
          entity_id: entityId,
        })
        .then(
          (resp) => this.setupStream(resp),
          (err) => console.error("Message failed!", err)
        );
    }
  }

  setupStream(resp) {
    this.opaqueId = "streaming-" + Janus.randomString(12);
    this.janus = new Janus({
      server: resp.server,
      apisecret: resp.apisecret,
      iceServers: resp.ice_servers || [
        { url: "stun:stun.voip.eutelia.it:3478" },
        { url: "stun:stun.l.google.com:19302" },
      ],
      success: () => {
        this.janus.attach({
          plugin: "janus.plugin.streaming",
          opaqueId: this.opaqueId,
          success: (pluginHandle) => {
            this.handle = pluginHandle;
            const body = { request: "watch", id: resp.stream_id };
            this.handle.send({ message: body });
          },
          error: function (error) {
            Janus.error("  -- Error attaching plugin... ", error);
          },
          onmessage: (msg, jsep) => {
            Janus.debug(" ::: Got a message :::");
            Janus.debug(msg);
            const result = msg["result"];
            if (result !== null && result !== undefined) {
              if (result["status"] !== undefined && result["status"] !== null) {
                const status = result["status"];
                if (status === "starting")
                  Janus.log("Starting, please wait...");
                else if (status === "started") Janus.log("Started");
                else if (status === "stopped") {
                  const body = { request: "stop" };
                  this.handle.send({ message: body });
                  this.handle.hangup();
                }
              }
            } else if (msg["error"] !== undefined && msg["error"] !== null) {
              const body = { request: "stop" };
              this.handle.send({ message: body });
              this.handle.hangup();
              return;
            }
            if (jsep !== undefined && jsep !== null) {
              this.handle.createAnswer({
                jsep: jsep,
                media: { audioSend: false, videoSend: false },
                success: (jsep) => {
                  const body = { request: "start" };
                  this.handle.send({
                    message: body,
                    jsep: jsep,
                  });
                },
                error: (error) => {
                  Janus.error("WebRTC error:", error);
                },
              });
            }
          },
          onremotestream: (stream) => {
            Janus.attachMediaStream(this.remoteVideo, stream);
          },
          oncleanup: function () {
            Janus.log(" ::: Got a cleanup notification :::");
          },
        });
      },
      error: function (error) {
        Janus.error(error);
      },
      destroyed: function () {},
    });
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("You need to define an entity");
    }
    this.config = config;
  }

  getCardSize() {
    return 5;
  }
}

Janus.init({
  dependencies: Janus.useDefaultDependencies(),
  callback: function () {
    customElements.define("janus-camera", JanusCard);
  },
});
