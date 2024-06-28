import { FormEvent, useState, useRef, useEffect } from 'react';
import { getStorage, ref, uploadBytes, getDownloadURL, getBlob } from "firebase/storage";
import { initializeApp } from "firebase/app";
import { useMutation } from '@tanstack/react-query';
import Image from 'next/image';
import { v4 as uuid } from 'uuid';
import { FileUploader } from "react-drag-drop-files";
import { FiPlus } from "react-icons/fi";

import useAppStore from '../useAppStore';
import { IConversation } from '@/utils/interfaces';
import Humana_Logo from "../assets/humana-logo.png";

const fileTypes = ['PDF'];

const firebaseConfig = {
  apiKey: "AIzaSyCp9haylJ8faYTfFnWFR-WTFlFC9Rt_JpA",
  authDomain: "healthharmony-d0b06.firebaseapp.com",
  projectId: "healthharmony-d0b06",
  storageBucket: "healthharmony-d0b06.appspot.com",
  messagingSenderId: "827302285181",
  appId: "1:827302285181:web:de7e812ff6bb9cc1408614"
};

const app = initializeApp(firebaseConfig);
const storage = getStorage(app);


function App() {
  const containerRef = useRef<HTMLDivElement>(null);

  const uploadedFiles = useAppStore(state => state.uploadedFiles);
  const setUploadedFiles = useAppStore(state => state.setUploadedFiles);

  const selectedFile = useAppStore(state => state.selectedFile);
  const setSelectedFile = useAppStore(state => state.setSelectedFile);

  const [conversations, setConversations] = useState<IConversation[]>([])

  const [questionInput, setQuestionInput] = useState('');
  const [searchInput, setSearchInput] = useState('');

  const handleQuestionAsked = async (evt: FormEvent<HTMLFormElement>) => {
    evt.preventDefault();
    if (!selectedFile) return;
    const question: IConversation = { text: questionInput, type: 'question' };

    setConversations(conversations => [...conversations, question]);

    await mutation.mutate({ file: selectedFile?.file, question: question.text });
  }

  const handleSearch = async (evt: FormEvent<HTMLFormElement>) => {
    evt.preventDefault();
    const filePath = `pdfs/${searchInput}.pdf`;
    const storageRef = ref(storage, filePath);

    try {
      const blob = await getBlob(storageRef);
      const file = new File([blob], `${searchInput}.pdf`, { type: blob.type });

      const fileUrl = URL.createObjectURL(blob);

      const newFile = {
        id: uuid(),
        url: fileUrl,
        file
      };

      reset();

      setUploadedFiles([...uploadedFiles, newFile]);
      setSelectedFile(newFile);
    } catch (error) {
      if (error.code === 'storage/object-not-found') {
        console.error('File not found');
      } else {
        console.error('Error getting download URL:', error);
      }
    }
  };

  const checkFileExists = async (filePath: string) => {
    const storageRef = ref(storage, filePath);
    try {
      const url = await getDownloadURL(storageRef);
      return url;
    } catch (error: any) {
      if (error.code === 'storage/object-not-found') {
        return null; // File does not exist
      } else {
        throw error; // Some other error occurred
      }
    }
  };

  const handleFileUpload = async (file: File) => {
    const filePath = `pdfs/${file.name}`;
    const existingUrl = await checkFileExists(filePath);

    if (existingUrl) {
      console.log('File already exists at', existingUrl);
    } else {
      const storageRef = ref(storage, filePath);
      uploadBytes(storageRef, file).then((snapshot) => {
        getDownloadURL(snapshot.ref).then((downloadURL) => {
          console.log('File available at', downloadURL);
        }).catch((error) => {
        });
      }).catch((error) => {
      });
    }

    const fileUrl = URL.createObjectURL(file);

    const newFile = {
      id: uuid(),
      url: fileUrl,
      file
    };

    reset();

    setUploadedFiles([...uploadedFiles, newFile]);
    setSelectedFile(newFile);
  };

  const reset = () => {
    setSelectedFile(null);
    setQuestionInput('');
    setConversations([])
  }

  const mutation = useMutation({
    mutationFn: async ({ file, question }: { file: File, question: string }) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('prompt', question);
      formData.append('name', file.n)

      const response = await fetch('http://127.0.0.1:5328/api/process_prompt', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result;
    },
    onSuccess: (result) => {
      const answer: IConversation = { text: result.answer, type: 'answer' };
      setConversations(conversations => [...conversations, answer]);
    },
    onError: (error) => {
      // Handle error logic
      console.error('Error:', error);
    },
    onSettled: () => {
      setQuestionInput('');
    }
  });

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: "smooth",
      })
    }
  });

  return (
    <div className='w-full h-screen flex flex-col justify-between'>
      <div className="navbar px-12 py-4 text-black bg-white">
        <div className="navbar-start">
          <a href="/">
            <Image src={Humana_Logo} alt='Humana H Logo' width={200} />
          </a>
        </div>

        <div className="navbar-end w-full flex justify-end">
          <ul className="gap-x-8 hidden lg:flex">
            <li><a href="https://www.humana.com/" target="_blank">EOC Documentation</a></li>
            <li><a href="https://www.humana.com/" target="_blank">Strider</a></li>
            <li><a href="https://www.humana.com/" target="_blank">More</a></li>
          </ul>

          <div className="dropdown dropdown-end lg:hidden">
            <label tabIndex={0} className="btn btn-ghost btn-circle">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h7" /></svg>
            </label>
            <ul tabIndex={0} className="menu menu-sm dropdown-content mt-3 z-[1] p-2 shadow bg-white rounded-box w-52">
              <li><a href="https://www.humana.com/" target="_blank">EOC Documentation</a></li>
              <li><a href="https://www.humana.com/" target="_blank">Strider</a></li>
              <li><a href="https://www.humana.com/" target="_blank">More</a></li>
            </ul>
          </div>
        </div>
      </div>

      {mutation.error && <div className="relative">
        <div className="z-10 absolute top-0 left-0 w-full h-full"></div>

        <div className="z-20 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 p-4 rounded-lg w-full max-w-xl">
          <div className="alert alert-error">
            <button onClick={() => mutation.reset()}><svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg></button>
            <p>Something went wrong, please try again later!</p>
          </div>
        </div>
      </div>}

      <div className="flex w-full max-h-full h-full overflow-y-hidden">
        <div className="w-1/6 bg-gray-100 p-2 space-y-4">
          <div className="flex gap-2 justify-between items-center">
            <div className='w-full h-full'>
              <button
                className="btn rounded-xl md:w-full bg-white border-none text-black shadow-md hover:bg-gray-100 w-full h-full"
                onClick={() => reset()}
              >
                <FiPlus />
                <p>New Chat</p>
              </button>
            </div>
          </div>

          {uploadedFiles.toReversed().map((elm, index) => (
            <div key={index} className="flex gap-2 justify-between items-center" onClick={() => setSelectedFile(elm)}>
              <button className={`btn rounded-xl md:w-full bg-[#78BE20] text-white border-none shadow-md hover:bg-[#5C9A1B] ${selectedFile?.id !== elm.id ? 'bg-opacity-25' : ''}`}>
                <p className='truncate'>{elm.file.name}</p>
              </button>
            </div>
          ))}
        </div>

        <div className="w-2/6 bg-gray-100 border border-gray-300 border-y-0">
          {selectedFile ? (<object data={selectedFile.url} type="application/pdf" width="100%" height="100%">
            <p>Alternative text - include a link <a href="https://www.clickdimensions.com/links/TestPDFfile.pdf">to the PDF!</a></p>
          </object>) : (
            <FileUploader
              handleChange={handleFileUpload}
              name="file"
              types={fileTypes}
              className={'w-full h-full border-none outline-none'}
            >
              <div className='w-full h-full flex flex-col justify-center items-center space-y-3'>
                <p>Upload a pdf to see it here!</p>

                <p className='text-sm'>Or</p>

                <form onSubmit={handleSearch} className="h-8 mt-2 flex justify-center input-group">
                  <input placeholder="Search by plan number" onChange={(evt) => (setSearchInput(evt.target.value))} value={searchInput} className="input max-w-3xl w-full mx-auto h-full bg-gray-200 focus:outline-none rounded-full focus:border-none text-center" />

                </form>
              </div>


            </FileUploader>
          )}
        </div>

        <div className="w-3/6 bg-gray-100 p-2 flex flex-col">
          <div ref={containerRef} className="flex-grow overflow-y-auto">
            {conversations.map((elm, index) => (
              elm.type === 'question' ? (<div key={index} className={`chat chat-end`}>
                <div className="chat-bubble bg-[#78BE20] bg-opacity-25 text-black">
                  <p>{elm.text}</p>
                </div>
              </div>) : (<div key={index} className={`chat chat-start`}>
                <div className="chat-bubble bg-gray-200 text-black">
                  <p>{elm.text}</p>
                </div>
              </div>)
            ))}

            {mutation.isPending && (<div className='p-4'>
              <span className="loading loading-dots loading-md text-gray-400"></span>
            </div>)}
          </div>

          <form onSubmit={handleQuestionAsked} className="h-16 mt-2 flex justify-center input-group">
            <input placeholder="Ask me a question" value={questionInput} onChange={(evt) => setQuestionInput(evt.target.value)} className="input max-w-3xl w-full mx-auto h-full bg-gray-200 focus:outline-none rounded-full focus:border-none" />

          </form>
        </div>
      </div>

      <div className="bg-[#78BE20] text-white text-xs sm:text-sm sm:py-2">
        <div className="w-3/4 mx-auto flex flex-wrap justify-center items-center">
          <a href="https://www.humana.com/" target="_blank" className="m-2">© 2024 Humana</a>
        </div>
      </div>
    </div>
  )
}

export default App;