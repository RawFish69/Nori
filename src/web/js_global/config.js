const NoriConfig = {
    domain: {
        base: "https://nori.fish",
        wynn: "https://nori.fish/wynn",
        docs: "https://nori.fish/docs",
        demo: "https://nori.fish/demo",
        chat: "https://nori.fish/chat"
    },
    
    links: {
        discord: "https://discord.gg/eDssA6Jbwd",
        discordBot: "https://discord.com/application-directory/873677970928193568",
        github: "https://github.com/RawFish69/Nori",
        youtube: "https://www.youtube.com/@RawFish69"
    },
    
    text: {
        siteName: "Nori-Web",
        footerText: "© 2024-2025 RawFish. Web URL: nori.fish",
        wynncraftName: "Nori-Wynn"
    },
    
    resources: {
        logo: "resources/nori_logo.png",
        favicon: "fish_logo.png"
    },

    navigation: {
        default: [
            { text: "Home", url: "/" },
            { text: "Wynn", url: "/wynn" },
            { text: "Docs", url: "/docs" },
            { text: "Support", url: "https://discord.gg/eDssA6Jbwd", external: true },
            { text: "Game", url: "https://game.nori.fish", external: true, special: "game-link", target: "_blank" },
            { text: "Demo", url: "/demo" },
        ],
        wynn: [
            { text: "Home", url: "/" },
            { text: "Wynn", url: "/wynn" },
            { text: "Docs", url: "/docs" },
            { text: "Support", url: "https://discord.gg/eDssA6Jbwd", external: true },
            { text: "Game", url: "https://game.nori.fish", external: true, special: "game-link", target: "_blank" },
            { text: "Demo", url: "/demo" }
        ]
    }
};

if (typeof window !== 'undefined') {
    window.NoriConfig = NoriConfig;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = NoriConfig;
}
