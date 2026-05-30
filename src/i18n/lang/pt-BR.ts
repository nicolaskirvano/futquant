import type { UIStrings } from "../types";

export default {
  nav: {
    home: "Inicio",
    posts: "Posts",
    tags: "Tags",
    about: "Sobre",
    archives: "Arquivo",
    search: "Busca",
  },
  post: {
    publishedAt: "Publicado em",
    updatedAt: "Atualizado",
    sharePostIntro: "Compartilhar:",
    sharePostOn: "Compartilhar no {{platform}}",
    sharePostViaEmail: "Compartilhar por email",
    tagLabel: "Tags",
    backToTop: "Voltar ao topo",
    goBack: "Voltar",
    editPage: "Editar pagina",
    previousPost: "Post anterior",
    nextPost: "Proximo post",
  },
  pagination: {
    prev: "Anterior",
    next: "Proxima",
    page: "Pagina",
  },
  home: {
    socialLinks: "Redes",
    featured: "Destaques",
    recentPosts: "Posts recentes",
    allPosts: "Todos os posts",
  },
  footer: {
    copyright: "Copyright",
    allRightsReserved: "Todos os direitos reservados.",
    privacy: "Privacidade",
    terms: "Termos de uso",
    contact: "Contato",
  },
  pages: {
    tagTitle: "Tag",
    tagDesc: "Todos os artigos com a tag",

    tagsTitle: "Tags",
    tagsDesc: "Todas as tags usadas nos posts.",

    postsTitle: "Posts",
    postsDesc: "Dados, preços e previsões do mercado FUT, atualizados todos os dias.",

    archivesTitle: "Arquivo",
    archivesDesc: "Todos os posts arquivados.",

    searchTitle: "Busca",
    searchDesc: "Busque qualquer artigo...",
  },
  a11y: {
    skipToContent: "Pular para o conteudo",
    openMenu: "Abrir menu",
    closeMenu: "Fechar menu",
    toggleTheme: "Alternar tema",
    searchPlaceholder: "Buscar posts...",
    noResults: "Nenhum resultado encontrado",
    goToPreviousPage: "Ir para a pagina anterior",
    goToNextPage: "Ir para a proxima pagina",
  },
  notFound: {
    title: "404 Nao encontrado",
    message: "Pagina nao encontrada",
    goHome: "Voltar para o inicio",
  },
} satisfies UIStrings;
